"""
LexIntellectus - QR Code Automation & Cryptographic Validation API
Provides endpoints to generate signed QR certificates for Reports, Invoices,
Documents/Signatures, and Legal Cases, plus a public verification endpoint.
"""

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import Usuario
from app.models.tenant import Despacho
from app.models.case import Expediente, PlazoFatal
from app.models.billing import Factura
from app.models.document import Documento, DocumentoFirma
from app.services.qr_verification_service import qr_verification_service

router = APIRouter(prefix="/qr", tags=["QR Verification & Automation"])


def _build_verify_url(request: Request, token: str) -> str:
    """Construye la URL pública de validación `/verify?token=...`."""
    origin = request.headers.get("origin")
    if not origin:
        host = request.headers.get("host", "localhost:3000")
        scheme = request.url.scheme or "http"
        if "8000" in host:
            host = host.replace("8000", "3000")
        origin = f"{scheme}://{host}"
    return f"{origin.rstrip('/')}/verify?token={token}"


@router.get("/report")
async def generate_report_qr(
    request: Request,
    period: str = Query("month", pattern="^(week|month|quarter|year)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Genera un Sello QR Criptográfico (HMAC-SHA256) para certificar un Reporte Ejecutivo
    del despacho con sus métricas exactas al momento de la emisión.
    """
    tenant_id = current_user.tenant_id
    today = date.today()

    tenant_res = await db.execute(select(Despacho).where(Despacho.id == tenant_id))
    tenant = tenant_res.scalar_one_or_none()

    active_cases = await db.scalar(
        select(func.count()).where(
            Expediente.tenant_id == tenant_id,
            Expediente.fecha_cierre == None,
        )
    ) or 0

    total_cases = await db.scalar(
        select(func.count()).where(Expediente.tenant_id == tenant_id)
    ) or 0

    total_closed = await db.scalar(
        select(func.count()).where(
            Expediente.tenant_id == tenant_id,
            Expediente.fecha_cierre != None,
        )
    ) or 0

    pending_deadlines = await db.scalar(
        select(func.count())
        .select_from(PlazoFatal)
        .join(Expediente)
        .where(
            Expediente.tenant_id == tenant_id,
            PlazoFatal.status == "pendiente",
        )
    ) or 0

    resolution_rate = round((total_closed / total_cases * 100), 1) if total_cases > 0 else 0.0
    issued_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    payload = {
        "entity_type": "report",
        "tenant_id": str(tenant_id),
        "despacho": tenant.nombre if tenant else "Despacho Legal",
        "period": period,
        "issued_at": issued_at,
        "issued_by": f"{current_user.nombre} {current_user.apellido}",
        "kpis": {
            "active_cases": active_cases,
            "total_cases": total_cases,
            "pending_deadlines": pending_deadlines,
            "resolution_rate": resolution_rate,
        },
    }

    signed = qr_verification_service.create_signed_token(payload)
    verify_url = _build_verify_url(request, signed["token"])
    qr_svg = qr_verification_service.generate_qr_svg_data_uri(verify_url)

    return {
        "entity_type": "report",
        "verification_code": signed["verification_code"],
        "sha256_hash": signed["sha256_hash"],
        "token": signed["token"],
        "verify_url": verify_url,
        "qr_svg_data_uri": qr_svg,
        "issued_at": issued_at,
        "despacho": payload["despacho"],
        "issued_by": payload["issued_by"],
        "kpis": payload["kpis"],
    }


@router.get("/invoice/{invoice_id}")
async def generate_invoice_qr(
    invoice_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Genera un Sello QR para una Factura que permite validar su autenticidad fiscal,
    consultar su estado de pago en tiempo real y automatizar el cobro móvil.
    """
    inv_res = await db.execute(
        select(Factura).where(
            Factura.id == invoice_id,
            Factura.tenant_id == current_user.tenant_id,
        )
    )
    inv = inv_res.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    if current_user.tipo_usuario == "cliente" and inv.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para esta factura")

    tenant_res = await db.execute(select(Despacho).where(Despacho.id == inv.tenant_id))
    tenant = tenant_res.scalar_one_or_none()

    issued_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    payload = {
        "entity_type": "invoice",
        "entity_id": str(inv.id),
        "tenant_id": str(inv.tenant_id),
        "despacho": tenant.nombre if tenant else "Despacho Legal",
        "numero_factura": inv.numero_factura,
        "moneda": inv.moneda,
        "total_factura": float(inv.total_factura or 0),
        "neto_a_pagar": float(inv.neto_a_pagar or 0),
        "fecha_emision": str(inv.fecha_emision),
        "issued_at": issued_at,
    }

    signed = qr_verification_service.create_signed_token(payload)
    verify_url = _build_verify_url(request, signed["token"])
    qr_svg = qr_verification_service.generate_qr_svg_data_uri(verify_url)

    return {
        "entity_type": "invoice",
        "entity_id": str(inv.id),
        "numero_factura": inv.numero_factura,
        "estado_actual": inv.estado,
        "verification_code": signed["verification_code"],
        "sha256_hash": signed["sha256_hash"],
        "token": signed["token"],
        "verify_url": verify_url,
        "qr_svg_data_uri": qr_svg,
        "issued_at": issued_at,
    }


@router.get("/document/{document_id}")
async def generate_document_qr(
    document_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Genera un Sello QR para validar la integridad de un documento legal y sus
    firmas electrónicas registradas en la bóveda documental.
    """
    doc_res = await db.execute(
        select(Documento).where(
            Documento.id == document_id,
            Documento.tenant_id == current_user.tenant_id,
        )
    )
    doc = doc_res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    sig_res = await db.execute(
        select(DocumentoFirma)
        .where(DocumentoFirma.documento_id == doc.id)
        .order_by(DocumentoFirma.signed_at.desc())
    )
    latest_sig = sig_res.scalars().first()

    issued_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    payload = {
        "entity_type": "document",
        "entity_id": str(doc.id),
        "tenant_id": str(doc.tenant_id),
        "nombre_archivo": doc.nombre_archivo,
        "categoria": doc.categoria,
        "firma_hash": latest_sig.firma_hash if latest_sig else None,
        "signed_at": latest_sig.signed_at.isoformat() if latest_sig and latest_sig.signed_at else None,
        "issued_at": issued_at,
    }

    signed = qr_verification_service.create_signed_token(payload)
    verify_url = _build_verify_url(request, signed["token"])
    qr_svg = qr_verification_service.generate_qr_svg_data_uri(verify_url)

    return {
        "entity_type": "document",
        "entity_id": str(doc.id),
        "nombre_archivo": doc.nombre_archivo,
        "firmado": bool(latest_sig),
        "firma_hash": latest_sig.firma_hash if latest_sig else None,
        "verification_code": signed["verification_code"],
        "sha256_hash": signed["sha256_hash"],
        "token": signed["token"],
        "verify_url": verify_url,
        "qr_svg_data_uri": qr_svg,
        "issued_at": issued_at,
    }


@router.get("/case/{case_id}")
async def generate_case_qr(
    case_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Genera una Ficha QR para un expediente o asunto legal, permitiendo acceso rápido
    desde dispositivos móviles en juzgados y validación de carátula.
    """
    case_res = await db.execute(
        select(Expediente).where(
            Expediente.id == case_id,
            Expediente.tenant_id == current_user.tenant_id,
        )
    )
    case = case_res.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    if current_user.tipo_usuario == "cliente" and case.cliente_principal_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    issued_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    payload = {
        "entity_type": "case",
        "entity_id": str(case.id),
        "tenant_id": str(case.tenant_id),
        "numero_interno": case.numero_interno,
        "numero_causa": case.numero_causa,
        "tipo_servicio": case.tipo_servicio,
        "issued_at": issued_at,
    }

    signed = qr_verification_service.create_signed_token(payload)
    verify_url = _build_verify_url(request, signed["token"])
    qr_svg = qr_verification_service.generate_qr_svg_data_uri(verify_url)

    return {
        "entity_type": "case",
        "entity_id": str(case.id),
        "numero_interno": case.numero_interno,
        "numero_causa": case.numero_causa,
        "verification_code": signed["verification_code"],
        "sha256_hash": signed["sha256_hash"],
        "token": signed["token"],
        "verify_url": verify_url,
        "qr_svg_data_uri": qr_svg,
        "issued_at": issued_at,
    }


@router.get("/verify")
async def public_verify_qr_token(
    token: str = Query(..., min_length=10),
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint Público de Validación Criptográfica (No requiere login).
    Al escanear cualquier código QR emitido por LexIntellectus (Reporte, Factura,
    Documento Firmado o Expediente), valida su firma HMAC-SHA256 y consulta el
    estado en tiempo real en la base de datos.
    """
    verified = qr_verification_service.verify_signed_token(token)
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código QR o sello criptográfico es inválido o ha sido alterado.",
        )

    payload = verified["payload"]
    entity_type = payload.get("entity_type")
    live_status = {}

    if entity_type == "invoice" and payload.get("entity_id"):
        inv_res = await db.execute(
            select(Factura).where(Factura.id == UUID(payload["entity_id"]))
        )
        inv = inv_res.scalar_one_or_none()
        if inv:
            live_status = {
                "estado_actual": inv.estado,
                "numero_factura": inv.numero_factura,
                "neto_a_pagar": float(inv.neto_a_pagar or 0),
                "moneda": inv.moneda,
                "fecha_vencimiento": str(inv.fecha_vencimiento),
                "action_url": "/portal/billing",
            }
    elif entity_type == "document" and payload.get("entity_id"):
        doc_res = await db.execute(
            select(Documento).where(Documento.id == UUID(payload["entity_id"]))
        )
        doc = doc_res.scalar_one_or_none()
        sig_res = await db.execute(
            select(DocumentoFirma)
            .where(DocumentoFirma.documento_id == UUID(payload["entity_id"]))
            .order_by(DocumentoFirma.signed_at.desc())
        )
        sigs = sig_res.scalars().all()
        if doc:
            live_status = {
                "nombre_archivo": doc.nombre_archivo,
                "categoria": doc.categoria,
                "total_firmas_electronicas": len(sigs),
                "ultima_firma_hash": sigs[0].firma_hash if sigs else None,
                "ultima_firma_fecha": sigs[0].signed_at.isoformat() if sigs and sigs[0].signed_at else None,
            }
    elif entity_type == "case" and payload.get("entity_id"):
        case_res = await db.execute(
            select(Expediente).where(Expediente.id == UUID(payload["entity_id"]))
        )
        case = case_res.scalar_one_or_none()
        if case:
            live_status = {
                "numero_interno": case.numero_interno,
                "numero_causa": case.numero_causa,
                "tipo_servicio": case.tipo_servicio,
                "juzgado": case.juzgado,
                "prioridad": case.prioridad,
                "activo": case.fecha_cierre is None,
                "action_url": f"/dashboard/cases/{case.id}",
            }
    elif entity_type == "report":
        live_status = {
            "despacho": payload.get("despacho"),
            "periodo_auditado": payload.get("period"),
            "emitido_por": payload.get("issued_by"),
            "metricas_certificadas": payload.get("kpis", {}),
        }

    return {
        "valid": True,
        "issuer": "LexIntellectus ERP — Autoridad de Certificación Criptográfica",
        "verification_code": verified["verification_code"],
        "sha256_hash": verified["sha256_hash"],
        "entity_type": entity_type,
        "issued_at": payload.get("issued_at"),
        "signed_payload": payload,
        "live_status": live_status,
        "verified_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    }
