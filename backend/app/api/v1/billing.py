"""
LexIntellectus ERP - Billing API Router
Sprint 5 — Time Tracking + Facturación
Handles Service Contracts (AFAs), Time Tracking, and dynamic invoicing with:
- Nicaragua local tax rules (DGI/ALMA withholdings, simplified non-VAT tax regimes)
- Client VAT exemptions
- Variable credit terms with dynamic late fees/moratory interests.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
import sqlalchemy as sa
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rbac import require_any_permission
from app.models.user import Usuario
from app.models.case import Expediente
from app.models.tenant import Despacho
from app.models.client import PerfilCliente
from app.models.professional import PerfilProfesional
from app.models.billing import ContratoServicio, RegistroTiempo, Factura, LineaFactura
from app.schemas.billing import (
    ContratoServicioCreate, ContratoServicioResponse, ContratoServicioUpdate,
    RegistroTiempoCreate, RegistroTiempoResponse, RegistroTiempoUpdate,
    FacturaCreate, FacturaResponse, FacturaUpdateStatus
)
from app.services.webhook_service import webhook_service

router = APIRouter(prefix="/billing", tags=["Billing & Monetization"])


# Helper function to calculate moratory interests dynamically
async def calculate_and_update_moratory_interests(invoice: Factura, db: AsyncSession) -> Factura:
    """
    Checks if credit invoice is overdue. If so, calculates the dynamic monthly moratory interest 
    and updates the database fields in real time on retrieval.
    """
    today = date.today()
    if invoice.estado in ('enviada', 'vencida') and invoice.es_credito and invoice.fecha_vencimiento < today:
        # Update state to vencida if not already
        if invoice.estado != 'vencida':
            invoice.estado = 'vencida'
        
        # Calculate interest
        # Formula: subtotal * (tasa_interes_moratorio / 100) * (dias_atraso / 30)
        dias_atraso = (today - invoice.fecha_vencimiento).days
        tasa_mensual = Decimal(str(invoice.tasa_interes_moratorio)) / Decimal("100.00")
        
        if tasa_mensual > 0 and dias_atraso > 0:
            interes_acumulado = invoice.subtotal * tasa_mensual * (Decimal(dias_atraso) / Decimal("30.00"))
            invoice.monto_interes_moratorio = interes_acumulado.quantize(Decimal("0.01"))
            
            # Recalculate net payable
            invoice.neto_a_pagar = (
                invoice.total_factura + 
                invoice.monto_interes_moratorio - 
                invoice.retencion_ir_monto - 
                invoice.retencion_alma_monto
            ).quantize(Decimal("0.01"))
            
            db.add(invoice)
            await db.flush()
            
    return invoice


# =========================================================================
# CONTRATO SERVICIO (AFAs) ENDPOINTS
# =========================================================================

@router.post("/contracts", response_model=ContratoServicioResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_contract(
    request: Request,
    contract_in: ContratoServicioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission("cases.update", "reports.read"))
):
    tenant_id = request.state.tenant_id
    
    # Check if case exists and belongs to tenant
    case_res = await db.execute(select(Expediente).where(
        Expediente.id == contract_in.case_id,
        Expediente.tenant_id == tenant_id
    ))
    case = case_res.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
        
    # Check if contract already exists for this case
    contract_res = await db.execute(select(ContratoServicio).where(ContratoServicio.case_id == contract_in.case_id))
    contract = contract_res.scalar_one_or_none()
    
    if contract:
        # Update existing
        for field, value in contract_in.dict(exclude_unset=True).items():
            setattr(contract, field, value)
    else:
        # Create new
        contract = ContratoServicio(
            tenant_id=tenant_id,
            **contract_in.dict()
        )
        db.add(contract)
        
    await db.commit()
    await db.refresh(contract)
    return contract


@router.get("/contracts/{case_id}", response_model=ContratoServicioResponse)
async def get_case_contract(
    request: Request,
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission("cases.read", "reports.read"))
):
    tenant_id = request.state.tenant_id
    
    contract_res = await db.execute(select(ContratoServicio).where(
        ContratoServicio.case_id == case_id,
        ContratoServicio.tenant_id == tenant_id
    ))
    contract = contract_res.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato de servicio no encontrado para este expediente")
        
    return contract


# =========================================================================
# REGISTRO TIEMPO (TIME TRACKING) ENDPOINTS
# =========================================================================

@router.post("/time-entries", response_model=RegistroTiempoResponse, status_code=status.HTTP_201_CREATED)
async def create_time_entry(
    request: Request,
    entry_in: RegistroTiempoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission("cases.update", "reports.read"))
):
    tenant_id = request.state.tenant_id
    
    # Check if case exists and belongs to tenant
    case_res = await db.execute(select(Expediente).where(
        Expediente.id == entry_in.case_id,
        Expediente.tenant_id == tenant_id
    ))
    case = case_res.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
        
    # Get contract for this case if exists to determine custom rates or schemes
    contract_res = await db.execute(select(ContratoServicio).where(ContratoServicio.case_id == entry_in.case_id))
    contract = contract_res.scalar_one_or_none()
    
    # Calculate applied hour rate
    tarifa = Decimal("0.00")
    if contract and contract.tarifa_hora_personalizada:
        tarifa = contract.tarifa_hora_personalizada
    else:
        # Lookup user profile hourly rate
        prof_res = await db.execute(select(PerfilProfesional).where(PerfilProfesional.user_id == current_user.id))
        prof = prof_res.scalar_one_or_none()
        if prof:
            tarifa = Decimal(str(prof.tarifa_hora_efectiva))
            if tarifa == 0:
                tarifa = Decimal(str(prof.tarifa_hora_nio))
        
        # Fallback to standard firm rate
        if tarifa == 0:
            tarifa = Decimal("50.00")  # NIO standard rate
            
    entry = RegistroTiempo(
        tenant_id=tenant_id,
        user_id=current_user.id,
        tarifa_aplicada=tarifa,
        facturado=False,
        **entry_in.dict()
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.get("/time-entries", response_model=List[RegistroTiempoResponse])
async def list_time_entries(
    request: Request,
    case_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
    facturado: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission("cases.read", "reports.read"))
):
    tenant_id = request.state.tenant_id
    
    query = select(RegistroTiempo).where(RegistroTiempo.tenant_id == tenant_id)
    if case_id:
        query = query.where(RegistroTiempo.case_id == case_id)
    if user_id:
        query = query.where(RegistroTiempo.user_id == user_id)
    if facturado is not None:
        query = query.where(RegistroTiempo.facturado == facturado)
        
    query = query.order_by(desc(RegistroTiempo.fecha_registro))
    res = await db.execute(query)
    return res.scalars().all()


@router.delete("/time-entries/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_entry(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission("cases.update", "reports.read"))
):
    tenant_id = request.state.tenant_id
    
    res = await db.execute(select(RegistroTiempo).where(
        RegistroTiempo.id == id,
        RegistroTiempo.tenant_id == tenant_id
    ))
    entry = res.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Registro de tiempo no encontrado")
        
    if entry.facturado:
        raise HTTPException(status_code=400, detail="No se puede eliminar un registro que ya ha sido facturado")
        
    await db.delete(entry)
    await db.commit()


# =========================================================================
# FACTURAS (INVOICES) ENDPOINTS
# =========================================================================

@router.post("/invoices/generate", response_model=FacturaResponse, status_code=status.HTTP_201_CREATED)
async def generate_invoice(
    request: Request,
    invoice_in: FacturaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission("cases.update", "reports.read"))
):
    tenant_id = request.state.tenant_id
    
    # 1. Fetch Tenant/Despacho tax config
    tenant_res = await db.execute(select(Despacho).where(Despacho.id == tenant_id))
    tenant = tenant_res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Despacho no encontrado")
        
    recauda_iva = tenant.config_json.get("recauda_iva", True) if tenant.config_json else True
    
    # 2. Fetch Client tax config
    client_profile_res = await db.execute(select(PerfilCliente).where(
        PerfilCliente.user_id == invoice_in.client_id,
        PerfilCliente.tenant_id == tenant_id
    ))
    client_profile = client_profile_res.scalar_one_or_none()
    
    es_exento_iva = client_profile.es_exento_iva if client_profile else False
    aplica_retenciones = client_profile.aplica_retenciones if client_profile else False
    
    # 3. Calculate breakdown of subtotals and items
    subtotal = Decimal("0.00")
    lineas_db = []
    
    for idx, line in enumerate(invoice_in.lineas):
        line_sub = Decimal(str(line.precio_unitario)) * Decimal(str(line.cantidad))
        subtotal += line_sub
        
        lineas_db.append(LineaFactura(
            descripcion=line.descripcion,
            cantidad=line.cantidad,
            precio_unitario=line.precio_unitario,
            subtotal=line_sub,
            tipo_item=line.tipo_item,
            es_exento=line.es_exento
        ))
        
    # Calculate IVA (15% in Nicaragua unless dispatch is exempt or client is exempt)
    iva_porcentaje = Decimal("15.00") if (recauda_iva and not es_exento_iva) else Decimal("0.00")
    iva_monto = Decimal("0.00")
    
    # Line level IVA calculation
    for line in lineas_db:
        if not line.es_exento:
            iva_monto += line.subtotal * (iva_porcentaje / Decimal("100.00"))
            
    iva_monto = iva_monto.quantize(Decimal("0.01"))
    total_factura = (subtotal + iva_monto).quantize(Decimal("0.01"))
    
    # Calculate DGI & ALMA withholdings (applied on professional services subtotal before VAT)
    retencion_ir_porcentaje = Decimal("0.00")
    retencion_ir_monto = Decimal("0.00")
    retencion_alma_porcentaje = Decimal("0.00")
    retencion_alma_monto = Decimal("0.00")
    
    if aplica_retenciones:
        # 10% IR withholding on Professional Services (honorarios) in Nicaragua
        # 1.5% ALMA municipal withholding
        subtotal_honorarios = sum(line.subtotal for line in lineas_db if line.tipo_item == 'honorario')
        
        if subtotal_honorarios > 0:
            retencion_ir_porcentaje = Decimal("10.00")
            retencion_ir_monto = (subtotal_honorarios * Decimal("0.10")).quantize(Decimal("0.01"))
            
            retencion_alma_porcentaje = Decimal("1.50")
            retencion_alma_monto = (subtotal_honorarios * Decimal("0.015")).quantize(Decimal("0.01"))
            
    # Calculate payment terms and Variable Credit conditions
    fecha_emision = date.today()
    dias_credito = invoice_in.dias_credito
    if client_profile and dias_credito == 0:
        dias_credito = client_profile.dias_credito_predeterminado
        
    fecha_vencimiento = datetime.combine(fecha_emision, datetime.min.time()).date()
    if dias_credito > 0:
        from datetime import timedelta
        fecha_vencimiento = fecha_emision + timedelta(days=dias_credito)
        
    tasa_interes = invoice_in.tasa_interes_moratorio
    if client_profile and tasa_interes == 0:
        tasa_interes = Decimal(str(client_profile.tasa_interes_moratorio_predeterminada))
        
    neto_a_pagar = (total_factura - retencion_ir_monto - retencion_alma_monto).quantize(Decimal("0.01"))
    
    # Generate sequential invoice number (e.g. FAC-00001) per tenant
    invoice_count_res = await db.execute(
        select(sa.func.count(Factura.id)).where(Factura.tenant_id == tenant_id)
    )
    invoice_count = invoice_count_res.scalar() or 0
    numero_factura = f"FAC-{invoice_count + 1:05d}"
    
    # Create Invoice ORM object
    factura = Factura(
        tenant_id=tenant_id,
        client_id=invoice_in.client_id,
        case_id=invoice_in.case_id,
        numero_factura=numero_factura,
        estado='borrador',
        fecha_emision=fecha_emision,
        fecha_vencimiento=fecha_vencimiento,
        es_credito=dias_credito > 0,
        dias_credito=dias_credito,
        subtotal=subtotal,
        iva_porcentaje=iva_porcentaje,
        iva_monto=iva_monto,
        retencion_ir_porcentaje=retencion_ir_porcentaje,
        retencion_ir_monto=retencion_ir_monto,
        retencion_alma_porcentaje=retencion_alma_porcentaje,
        retencion_alma_monto=retencion_alma_monto,
        tasa_interes_moratorio=tasa_interes,
        monto_interes_moratorio=Decimal("0.00"),
        total_factura=total_factura,
        neto_a_pagar=neto_a_pagar,
        moneda=invoice_in.moneda,
        lineas=lineas_db
    )
    
    db.add(factura)
    await db.flush()  # Fetch invoice ID
    
    # If a case_id was provided and billing is hourly, associate unbilled time entries to this invoice
    if invoice_in.case_id:
        await db.execute(
            update(RegistroTiempo)
            .where(
                RegistroTiempo.case_id == invoice_in.case_id,
                RegistroTiempo.facturado == False,
                RegistroTiempo.es_facturable == True,
                RegistroTiempo.tenant_id == tenant_id
            )
            .values(factura_id=factura.id)
        )
        
    factura_id = factura.id
    await db.commit()
    await webhook_service.dispatch_event(
        db=db,
        tenant_id=tenant_id,
        event_type="invoice.created",
        data={
            "factura_id": str(factura_id),
            "numero_factura": numero_factura,
            "total_factura": float(total_factura),
            "neto_a_pagar": float(neto_a_pagar),
            "moneda": invoice_in.moneda,
        },
    )
    from sqlalchemy.orm import selectinload
    inv_q = await db.execute(select(Factura).options(selectinload(Factura.lineas)).where(Factura.id == factura_id))
    return inv_q.scalar_one()


@router.get("/invoices", response_model=List[FacturaResponse])
async def list_invoices(
    request: Request,
    client_id: Optional[UUID] = Query(None),
    case_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission("cases.read", "reports.read"))
):
    tenant_id = request.state.tenant_id
    
    query = select(Factura).where(Factura.tenant_id == tenant_id)
    if client_id:
        query = query.where(Factura.client_id == client_id)
    if case_id:
        query = query.where(Factura.case_id == case_id)
    if estado:
        query = query.where(Factura.estado == estado)
        
    query = query.order_by(desc(Factura.fecha_emision))
    res = await db.execute(query)
    invoices = res.scalars().all()
    
    # Calculate moratory interest dynamically in real time for list
    updated_invoices = []
    for inv in invoices:
        updated_inv = await calculate_and_update_moratory_interests(inv, db)
        updated_invoices.append(updated_inv)
        
    if len(invoices) > 0:
        await db.commit()
        
    return updated_invoices


@router.get("/invoices/{id}", response_model=FacturaResponse)
async def get_invoice(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission("cases.read", "reports.read"))
):
    tenant_id = request.state.tenant_id
    
    res = await db.execute(select(Factura).where(
        Factura.id == id,
        Factura.tenant_id == tenant_id
    ))
    invoice = res.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
        
    # Calculate moratory interest dynamically in real time
    invoice = await calculate_and_update_moratory_interests(invoice, db)
    await db.commit()
    return invoice


@router.patch("/invoices/{id}/status", response_model=FacturaResponse)
async def update_invoice_status(
    request: Request,
    id: UUID,
    status_in: FacturaUpdateStatus,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission("cases.update", "reports.read"))
):
    tenant_id = request.state.tenant_id
    
    res = await db.execute(select(Factura).where(
        Factura.id == id,
        Factura.tenant_id == tenant_id
    ))
    invoice = res.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
        
    invoice.estado = status_in.estado
    
    # If state changes to pagada, update associated time entries to facturado=True
    if status_in.estado == 'pagada':
        await db.execute(
            update(RegistroTiempo)
            .where(RegistroTiempo.factura_id == invoice.id)
            .values(facturado=True)
        )
        
    inv_id = invoice.id
    inv_num = invoice.numero_factura
    inv_neto = float(invoice.neto_a_pagar or 0)
    inv_moneda = invoice.moneda
    await db.commit()
    if status_in.estado == 'pagada':
        await webhook_service.dispatch_event(
            db=db,
            tenant_id=tenant_id,
            event_type="invoice.paid",
            data={
                "factura_id": str(inv_id),
                "numero_factura": inv_num,
                "estado": "pagada",
                "neto_a_pagar": inv_neto,
                "moneda": inv_moneda,
            },
        )
    elif status_in.estado == 'vencida':
        await webhook_service.dispatch_event(
            db=db,
            tenant_id=tenant_id,
            event_type="invoice.overdue",
            data={
                "factura_id": str(inv_id),
                "numero_factura": inv_num,
                "estado": "vencida",
                "neto_a_pagar": inv_neto,
                "moneda": inv_moneda,
            },
        )
    from sqlalchemy.orm import selectinload
    inv_q = await db.execute(select(Factura).options(selectinload(Factura.lineas)).where(Factura.id == inv_id))
    return inv_q.scalar_one()


@router.get("/invoices/export/json")
async def export_invoices(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission("reports.read"))
):
    tenant_id = request.state.tenant_id
    
    res = await db.execute(select(Factura).where(Factura.tenant_id == tenant_id))
    invoices = res.scalars().all()
    
    export_data = []
    for inv in invoices:
        # Trigger dynamic moratory interest calculations
        inv = await calculate_and_update_moratory_interests(inv, db)
        
        export_data.append({
            "id": str(inv.id),
            "numero_factura": inv.numero_factura,
            "estado": inv.estado,
            "fecha_emision": str(inv.fecha_emision),
            "fecha_vencimiento": str(inv.fecha_vencimiento),
            "subtotal": float(inv.subtotal),
            "iva_monto": float(inv.iva_monto),
            "retencion_ir": float(inv.retencion_ir_monto),
            "retencion_alma": float(inv.retencion_alma_monto),
            "intereses_mora": float(inv.monto_interes_moratorio),
            "neto_pagar": float(inv.neto_a_pagar),
            "moneda": inv.moneda
        })
        
    await db.commit()
    return export_data


@router.get("/invoices/export/csv")
async def export_invoices_csv(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission("reports.read"))
):
    """Exporta todas las facturas del despacho en formato CSV estándar para software contable."""
    import io
    import csv
    from fastapi.responses import Response

    tenant_id = request.state.tenant_id
    res = await db.execute(select(Factura).where(Factura.tenant_id == tenant_id))
    invoices = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "numero_factura", "estado", "fecha_emision", "fecha_vencimiento",
        "moneda", "subtotal", "iva_monto", "retencion_ir", "retencion_alma",
        "intereses_mora", "neto_a_pagar"
    ])
    for inv in invoices:
        inv = await calculate_and_update_moratory_interests(inv, db)
        writer.writerow([
            inv.numero_factura,
            inv.estado,
            str(inv.fecha_emision),
            str(inv.fecha_vencimiento),
            inv.moneda,
            f"{float(inv.subtotal or 0):.2f}",
            f"{float(inv.iva_monto or 0):.2f}",
            f"{float(inv.retencion_ir_monto or 0):.2f}",
            f"{float(inv.retencion_alma_monto or 0):.2f}",
            f"{float(inv.monto_interes_moratorio or 0):.2f}",
            f"{float(inv.neto_a_pagar or 0):.2f}",
        ])
    await db.commit()
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=facturas_contabilidad.csv"},
    )
