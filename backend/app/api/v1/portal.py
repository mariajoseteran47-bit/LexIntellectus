from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import hashlib
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import decode_token
from app.models.user import Usuario
from app.models.case import Expediente, PlazoFatal
from app.models.document import Documento, DocumentoFirma
from app.models.billing import Factura
from app.models.collaboration import HiloDiscusion, MensajeHilo, AprobacionDocumento
from app.models.client import PerfilCliente
from app.schemas.case import ExpedienteResponse, ExpedienteListResponse
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.schemas.billing import FacturaResponse
from app.services.storage import storage_service
from app.services.calendar_service import CalendarService
from app.services.webhook_service import webhook_service
from app.core.rate_limit import default_rate_limiter

router = APIRouter(prefix="/portal", tags=["Client Portal"], dependencies=[Depends(default_rate_limiter)])


def require_client_role(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Ensure the logged-in user is a client."""
    if current_user.tipo_usuario != "cliente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso exclusivo para clientes",
        )
    return current_user


# =========================================================================
# SCHEMAS DEL PORTAL DEL CLIENTE
# =========================================================================

class DocumentSignRequest(BaseModel):
    signature_svg: str


class PortalThreadCreate(BaseModel):
    expediente_id: UUID
    titulo: str = Field(..., min_length=3, max_length=300)
    mensaje_inicial: str = Field(..., min_length=1)


class PortalMessageCreate(BaseModel):
    contenido: str = Field(..., min_length=1)


class PortalApprovalDecision(BaseModel):
    approval_id: Optional[UUID] = None
    estado: str = Field(..., pattern="^(aprobado|rechazado)$")
    comentarios: Optional[str] = None


class PortalProfileUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    direccion_domicilio: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    razon_social: Optional[str] = None
    nombre_comercial: Optional[str] = None


# =========================================================================
# 1. DASHBOARD CONSOLIDADO DEL PORTAL
# =========================================================================

@router.get("/dashboard")
async def get_portal_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role),
):
    """Resumen ejecutivo consolidado del cliente en el portal."""
    tenant_id = current_user.tenant_id

    cases_res = await db.execute(
        select(Expediente)
        .where(
            Expediente.tenant_id == tenant_id,
            Expediente.cliente_principal_id == current_user.id,
        )
        .order_by(desc(Expediente.created_at))
    )
    cases = cases_res.scalars().all()
    case_ids = [c.id for c in cases]

    invoices_res = await db.execute(
        select(Factura)
        .where(
            Factura.tenant_id == tenant_id,
            Factura.client_id == current_user.id,
            Factura.estado != "borrador",
        )
    )
    invoices = invoices_res.scalars().all()
    unpaid = [inv for inv in invoices if inv.estado not in ("pagada", "anulada")]
    total_usd = sum(float(inv.neto_a_pagar or 0) for inv in unpaid if inv.moneda == "USD")
    total_nio = sum(float(inv.neto_a_pagar or 0) for inv in unpaid if inv.moneda == "NIO")

    docs_count = 0
    pending_approvals = 0
    upcoming_deadlines = 0

    if case_ids:
        docs_count = await db.scalar(
            select(func.count(Documento.id)).where(
                Documento.tenant_id == tenant_id,
                Documento.expediente_id.in_(case_ids),
                Documento.es_confidencial == False,
            )
        ) or 0

        pending_approvals = await db.scalar(
            select(func.count(AprobacionDocumento.id)).where(
                AprobacionDocumento.tenant_id == tenant_id,
                or_(
                    AprobacionDocumento.aprobador_id == current_user.id,
                    AprobacionDocumento.expediente_id.in_(case_ids),
                ),
                AprobacionDocumento.estado == "pendiente",
            )
        ) or 0

        upcoming_deadlines = await db.scalar(
            select(func.count(PlazoFatal.id)).where(
                PlazoFatal.expediente_id.in_(case_ids),
                PlazoFatal.status == "pendiente",
            )
        ) or 0

    return {
        "active_cases": len(cases),
        "shared_documents": docs_count,
        "pending_invoices": len(unpaid),
        "total_pending_usd": round(total_usd, 2),
        "total_pending_nio": round(total_nio, 2),
        "pending_approvals": pending_approvals,
        "upcoming_deadlines": upcoming_deadlines,
    }


# =========================================================================
# 2. EXPEDIENTES / ASUNTOS DEL CLIENTE (/cases y /matters)
# =========================================================================

@router.get("/cases", response_model=ExpedienteListResponse)
@router.get("/matters", response_model=ExpedienteListResponse)
async def list_client_cases(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role)
):
    """List all legal cases where the logged-in user is the primary client."""
    tenant_id = current_user.tenant_id
    skip = (page - 1) * size

    query = select(Expediente).where(
        Expediente.tenant_id == tenant_id,
        Expediente.cliente_principal_id == current_user.id
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    if total == 0:
        return {"items": [], "total": 0, "page": page, "size": size}

    query = query.options(selectinload(Expediente.partes)).order_by(desc(Expediente.created_at)).offset(skip).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }


@router.get("/cases/{id}", response_model=ExpedienteResponse)
@router.get("/matters/{id}", response_model=ExpedienteResponse)
async def get_client_case(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role)
):
    """Retrieve details of a specific case, verifying client ownership."""
    tenant_id = current_user.tenant_id

    query = select(Expediente).options(selectinload(Expediente.partes)).where(
        Expediente.id == id,
        Expediente.tenant_id == tenant_id,
        Expediente.cliente_principal_id == current_user.id
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expediente no encontrado o sin autorización"
        )
    return case


# =========================================================================
# 3. DOCUMENTOS COMPARTIDOS Y FIRMA ELECTRÓNICA
# =========================================================================

@router.get("/documents", response_model=DocumentListResponse)
async def list_client_documents(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role)
):
    """List all non-confidential documents shared in the client's cases."""
    tenant_id = current_user.tenant_id

    query = (
        select(Documento)
        .join(Expediente)
        .where(
            Documento.tenant_id == tenant_id,
            Expediente.cliente_principal_id == current_user.id,
            Documento.es_confidencial == False
        )
        .order_by(desc(Documento.created_at))
    )

    result = await db.execute(query)
    docs = result.scalars().all()

    response_items = []
    for doc in docs:
        response_items.append(
            DocumentResponse(
                id=doc.id,
                expediente_id=doc.expediente_id,
                nombre_archivo=doc.nombre_archivo,
                tipo_archivo=doc.tipo_archivo,
                tamano_bytes=doc.tamano_bytes,
                created_at=doc.created_at,
                subido_por_id=doc.subido_por_id,
                descripcion=doc.descripcion,
                categoria=doc.categoria,
                tags=doc.tags
            )
        )

    return {
        "items": response_items,
        "total": len(response_items)
    }


@router.get("/documents/{id}/download")
async def download_client_document(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role)
):
    """Generate a secure, short-lived presigned URL to download a shared document."""
    tenant_id = current_user.tenant_id

    query = (
        select(Documento)
        .join(Expediente)
        .where(
            Documento.id == id,
            Documento.tenant_id == tenant_id,
            Expediente.cliente_principal_id == current_user.id,
            Documento.es_confidencial == False
        )
    )

    result = await db.execute(query)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado o sin autorización"
        )

    try:
        url = storage_service.get_presigned_url(doc.storage_path)
        return {"url": url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar enlace de descarga: {str(e)}"
        )


@router.post("/documents/{id}/sign")
async def sign_client_document(
    id: UUID,
    req: DocumentSignRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role)
):
    """Electronically sign a document in the client portal, generating a security audit trail."""
    tenant_id = current_user.tenant_id

    query = (
        select(Documento)
        .join(Expediente)
        .where(
            Documento.id == id,
            Documento.tenant_id == tenant_id,
            Expediente.cliente_principal_id == current_user.id,
            Documento.es_confidencial == False
        )
    )
    result = await db.execute(query)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado o sin autorización"
        )

    ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown")
    timestamp = datetime.utcnow()

    raw_payload = f"{doc.storage_path}|{current_user.id}|{ip}|{user_agent}|{req.signature_svg}|{timestamp.isoformat()}"
    signature_hash = hashlib.sha256(raw_payload.encode()).hexdigest()

    sig_id = uuid.uuid4()
    sig = DocumentoFirma(
        id=sig_id,
        tenant_id=tenant_id,
        documento_id=id,
        usuario_id=current_user.id,
        firma_hash=signature_hash,
        ip_address=ip,
        user_agent=user_agent,
        signature_svg=req.signature_svg,
        signed_at=timestamp
    )
    db.add(sig)

    current_tags = list(doc.tags) if doc.tags else []
    if "firmado" not in current_tags:
        current_tags.append("firmado")
        doc.tags = current_tags

    await db.commit()

    return {
        "status": "success",
        "message": "Documento firmado electrónicamente con éxito",
        "signature_id": sig_id,
        "hash": signature_hash,
        "signed_at": timestamp
    }


# =========================================================================
# 4. APROBACIÓN DOCUMENTAL EN EL PORTAL (/approvals)
# =========================================================================

@router.get("/approvals")
async def list_portal_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role),
):
    """Lista las solicitudes de aprobación de documentos vinculadas a los casos del cliente."""
    tenant_id = current_user.tenant_id

    cases_res = await db.execute(
        select(Expediente.id).where(
            Expediente.tenant_id == tenant_id,
            Expediente.cliente_principal_id == current_user.id,
        )
    )
    case_ids = [r[0] for r in cases_res.all()]

    filters = [AprobacionDocumento.aprobador_id == current_user.id]
    if case_ids:
        filters.append(AprobacionDocumento.expediente_id.in_(case_ids))

    query = (
        select(AprobacionDocumento)
        .options(
            selectinload(AprobacionDocumento.documento),
            selectinload(AprobacionDocumento.solicitante),
        )
        .where(
            AprobacionDocumento.tenant_id == tenant_id,
            or_(*filters),
        )
        .order_by(desc(AprobacionDocumento.created_at))
    )
    res = await db.execute(query)
    approvals = res.scalars().all()

    items = []
    for ap in approvals:
        items.append({
            "id": str(ap.id),
            "documento_id": str(ap.documento_id),
            "nombre_archivo": ap.documento.nombre_archivo if ap.documento else "Documento",
            "expediente_id": str(ap.expediente_id) if ap.expediente_id else None,
            "estado": ap.estado,
            "motivo_solicitud": ap.motivo_solicitud,
            "comentarios_aprobador": ap.comentarios_aprobador,
            "solicitante_nombre": (
                f"{ap.solicitante.nombre} {ap.solicitante.apellido}"
                if ap.solicitante else "Abogado del Despacho"
            ),
            "fecha_solicitud": ap.fecha_solicitud.isoformat() if ap.fecha_solicitud else None,
            "fecha_respuesta": ap.fecha_respuesta.isoformat() if ap.fecha_respuesta else None,
        })
    return {"items": items, "total": len(items)}


@router.post("/approvals")
@router.post("/approvals/{approval_id}/decision")
async def decide_portal_approval(
    body: PortalApprovalDecision,
    approval_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role),
):
    """Permite al cliente aprobar o rechazar formalmente un documento desde su portal."""
    target_id = approval_id or body.approval_id
    if not target_id:
        raise HTTPException(status_code=400, detail="approval_id es requerido")

    tenant_id = current_user.tenant_id
    query = (
        select(AprobacionDocumento)
        .options(selectinload(AprobacionDocumento.expediente))
        .where(
            AprobacionDocumento.id == target_id,
            AprobacionDocumento.tenant_id == tenant_id,
        )
    )
    res = await db.execute(query)
    ap = res.scalar_one_or_none()
    if not ap:
        raise HTTPException(status_code=404, detail="Solicitud de aprobación no encontrada")

    is_owner = (
        ap.aprobador_id == current_user.id
        or (ap.expediente and ap.expediente.cliente_principal_id == current_user.id)
    )
    if not is_owner:
        raise HTTPException(status_code=403, detail="Sin autorización para decidir esta aprobación")

    ap.estado = body.estado
    ap.comentarios_aprobador = body.comentarios
    ap.fecha_respuesta = datetime.utcnow()
    doc_id_str = str(ap.documento_id)
    exp_id_str = str(ap.expediente_id) if ap.expediente_id else None

    await db.commit()

    if body.estado == "aprobado":
        await webhook_service.dispatch_event(
            db=db,
            tenant_id=tenant_id,
            event_type="document.approved",
            data={
                "approval_id": str(target_id),
                "documento_id": doc_id_str,
                "expediente_id": exp_id_str,
                "aprobado_por": str(current_user.id),
                "origen": "portal_cliente",
            },
        )

    return {
        "status": "success",
        "id": str(target_id),
        "estado": body.estado,
        "comentarios_aprobador": body.comentarios,
        "fecha_respuesta": ap.fecha_respuesta.isoformat(),
    }


# =========================================================================
# 5. HILOS DE COMUNICACIÓN CLIENTE - ABOGADO (/threads)
# =========================================================================

@router.get("/threads")
async def list_portal_threads(
    expediente_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role),
):
    """Lista los hilos de conversación entre el cliente y su equipo legal (`tipo_canal='cliente'`)."""
    tenant_id = current_user.tenant_id

    cases_res = await db.execute(
        select(Expediente.id).where(
            Expediente.tenant_id == tenant_id,
            Expediente.cliente_principal_id == current_user.id,
        )
    )
    case_ids = [r[0] for r in cases_res.all()]
    if not case_ids:
        return {"items": [], "total": 0}

    query = (
        select(HiloDiscusion)
        .options(selectinload(HiloDiscusion.expediente), selectinload(HiloDiscusion.creado_por))
        .where(
            HiloDiscusion.tenant_id == tenant_id,
            HiloDiscusion.expediente_id.in_(case_ids),
            HiloDiscusion.tipo_canal == "cliente",
        )
    )
    if expediente_id:
        query = query.where(HiloDiscusion.expediente_id == expediente_id)

    query = query.order_by(desc(HiloDiscusion.updated_at))
    res = await db.execute(query)
    threads = res.scalars().all()

    items = []
    for t in threads:
        items.append({
            "id": str(t.id),
            "expediente_id": str(t.expediente_id),
            "numero_expediente": (
                t.expediente.numero_interno or t.expediente.numero_causa or "Asunto Legal"
                if t.expediente else "Asunto Legal"
            ),
            "titulo": t.titulo,
            "cerrado": t.cerrado,
            "total_mensajes": t.total_mensajes or 0,
            "creado_por_nombre": (
                f"{t.creado_por.nombre} {t.creado_por.apellido}" if t.creado_por else "Usuario"
            ),
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "ultimo_mensaje_at": t.ultimo_mensaje_at.isoformat() if t.ultimo_mensaje_at else None,
        })

    return {"items": items, "total": len(items)}


@router.post("/threads", status_code=status.HTTP_201_CREATED)
async def create_portal_thread(
    body: PortalThreadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role),
):
    """Inicia una nueva consulta o hilo de comunicación con el abogado titular del expediente."""
    tenant_id = current_user.tenant_id

    case_res = await db.execute(
        select(Expediente).where(
            Expediente.id == body.expediente_id,
            Expediente.tenant_id == tenant_id,
            Expediente.cliente_principal_id == current_user.id,
        )
    )
    case = case_res.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado o sin autorización")

    now = datetime.utcnow()
    hilo = HiloDiscusion(
        tenant_id=tenant_id,
        expediente_id=case.id,
        titulo=body.titulo,
        tipo_canal="cliente",
        cerrado=False,
        creado_por_id=current_user.id,
        total_mensajes=1,
        ultimo_mensaje_at=now,
    )
    db.add(hilo)
    await db.flush()

    msg = MensajeHilo(
        hilo_id=hilo.id,
        autor_id=current_user.id,
        contenido=body.mensaje_inicial,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(hilo)

    return {
        "id": str(hilo.id),
        "expediente_id": str(hilo.expediente_id),
        "titulo": hilo.titulo,
        "tipo_canal": hilo.tipo_canal,
        "total_mensajes": hilo.total_mensajes,
        "created_at": hilo.created_at.isoformat(),
    }


@router.get("/threads/{thread_id}/messages")
async def list_portal_thread_messages(
    thread_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role),
):
    """Obtiene los mensajes de un hilo de comunicación del cliente."""
    tenant_id = current_user.tenant_id

    thread_res = await db.execute(
        select(HiloDiscusion)
        .join(Expediente)
        .where(
            HiloDiscusion.id == thread_id,
            HiloDiscusion.tenant_id == tenant_id,
            HiloDiscusion.tipo_canal == "cliente",
            Expediente.cliente_principal_id == current_user.id,
        )
    )
    hilo = thread_res.scalar_one_or_none()
    if not hilo:
        raise HTTPException(status_code=404, detail="Hilo de conversación no encontrado")

    msgs_res = await db.execute(
        select(MensajeHilo)
        .options(selectinload(MensajeHilo.autor))
        .where(MensajeHilo.hilo_id == thread_id)
        .order_by(MensajeHilo.created_at.asc())
    )
    msgs = msgs_res.scalars().all()

    return {
        "thread_id": str(hilo.id),
        "titulo": hilo.titulo,
        "cerrado": hilo.cerrado,
        "messages": [
            {
                "id": str(m.id),
                "autor_id": str(m.autor_id),
                "autor_nombre": f"{m.autor.nombre} {m.autor.apellido}" if m.autor else "Usuario",
                "es_cliente": (m.autor_id == current_user.id),
                "contenido": m.contenido,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in msgs
        ],
    }


@router.post("/threads/{thread_id}/messages", status_code=status.HTTP_201_CREATED)
async def create_portal_thread_message(
    thread_id: UUID,
    body: PortalMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role),
):
    """Envía un mensaje nuevo del cliente a su abogado dentro de un hilo activo."""
    tenant_id = current_user.tenant_id

    thread_res = await db.execute(
        select(HiloDiscusion)
        .join(Expediente)
        .where(
            HiloDiscusion.id == thread_id,
            HiloDiscusion.tenant_id == tenant_id,
            HiloDiscusion.tipo_canal == "cliente",
            Expediente.cliente_principal_id == current_user.id,
        )
    )
    hilo = thread_res.scalar_one_or_none()
    if not hilo:
        raise HTTPException(status_code=404, detail="Hilo de conversación no encontrado")

    if hilo.cerrado:
        raise HTTPException(status_code=400, detail="Este hilo de consulta ya fue cerrado")

    now = datetime.utcnow()
    msg = MensajeHilo(
        hilo_id=hilo.id,
        autor_id=current_user.id,
        contenido=body.contenido,
    )
    db.add(msg)
    hilo.total_mensajes = (hilo.total_mensajes or 0) + 1
    hilo.ultimo_mensaje_at = now
    hilo.updated_at = now

    await db.commit()
    await db.refresh(msg)

    return {
        "id": str(msg.id),
        "hilo_id": str(hilo.id),
        "autor_id": str(current_user.id),
        "autor_nombre": f"{current_user.nombre} {current_user.apellido}",
        "es_cliente": True,
        "contenido": msg.contenido,
        "created_at": msg.created_at.isoformat() if msg.created_at else now.isoformat(),
    }


# =========================================================================
# 6. PERFIL DEL CLIENTE (/profile)
# =========================================================================

@router.get("/profile")
async def get_portal_profile(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role),
):
    """Obtiene los datos personales, corporativos y de facturación del cliente autenticado."""
    prof_res = await db.execute(
        select(PerfilCliente).where(
            PerfilCliente.user_id == current_user.id,
            PerfilCliente.tenant_id == current_user.tenant_id,
        )
    )
    perfil = prof_res.scalar_one_or_none()

    return {
        "id": str(current_user.id),
        "nombre": current_user.nombre,
        "apellido": current_user.apellido,
        "email": current_user.email,
        "telefono": current_user.telefono or "",
        "tipo_persona": perfil.tipo_persona if perfil else "natural",
        "cedula_identidad": perfil.cedula_identidad if perfil else "",
        "ruc": perfil.ruc if perfil else "",
        "razon_social": perfil.razon_social if perfil else "",
        "nombre_comercial": perfil.nombre_comercial if perfil else "",
        "direccion_domicilio": perfil.direccion_domicilio if perfil else "",
        "ciudad": perfil.ciudad if perfil else "Managua",
        "departamento": perfil.departamento if perfil else "Managua",
        "pais": perfil.pais if perfil else "Nicaragua",
        "segmento": perfil.segmento if perfil else "individual",
        "kyc_verificado": bool(perfil.kyc_verificado) if perfil else False,
        "dias_credito": perfil.dias_credito_predeterminado if perfil else 0,
    }


@router.patch("/profile")
async def update_portal_profile(
    body: PortalProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role),
):
    """Actualiza los datos de contacto y domicilio del cliente desde el portal."""
    if body.nombre is not None:
        current_user.nombre = body.nombre
    if body.apellido is not None:
        current_user.apellido = body.apellido
    if body.telefono is not None:
        current_user.telefono = body.telefono

    prof_res = await db.execute(
        select(PerfilCliente).where(
            PerfilCliente.user_id == current_user.id,
            PerfilCliente.tenant_id == current_user.tenant_id,
        )
    )
    perfil = prof_res.scalar_one_or_none()
    if not perfil:
        perfil = PerfilCliente(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            tipo_persona="natural",
        )
        db.add(perfil)

    if body.direccion_domicilio is not None:
        perfil.direccion_domicilio = body.direccion_domicilio
    if body.ciudad is not None:
        perfil.ciudad = body.ciudad
    if body.departamento is not None:
        perfil.departamento = body.departamento
    if body.razon_social is not None:
        perfil.razon_social = body.razon_social
    if body.nombre_comercial is not None:
        perfil.nombre_comercial = body.nombre_comercial

    await db.commit()
    return await get_portal_profile(db=db, current_user=current_user)


# =========================================================================
# 7. FACTURAS Y CALENDARIO ICAL (.ICS CON SOPORTE ?token=)
# =========================================================================

@router.get("/invoices", response_model=List[FacturaResponse])
async def list_client_invoices(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role)
):
    """List all published (non-draft) invoices for this client."""
    tenant_id = current_user.tenant_id

    query = (
        select(Factura)
        .options(selectinload(Factura.lineas))
        .where(
            Factura.tenant_id == tenant_id,
            Factura.client_id == current_user.id,
            Factura.estado != "borrador"
        )
        .order_by(desc(Factura.fecha_emision))
    )

    result = await db.execute(query)
    invoices = result.scalars().all()
    return invoices


@router.get("/calendar/ical.ics")
async def get_portal_ical(
    request: Request,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Export all deadlines for the client's cases in RFC 5545 iCalendar format.
    Supports both Authorization: Bearer <token> header and ?token=<jwt> query parameter
    so Google Calendar, Outlook, and Apple Calendar can subscribe via URL.
    """
    auth_header = request.headers.get("Authorization", "")
    raw_token = token
    if not raw_token and auth_header.startswith("Bearer "):
        raw_token = auth_header.split(" ", 1)[1].strip()

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudieron validar las credenciales",
        )

    payload = decode_token(raw_token)
    if not payload or not payload.get("sub") or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )

    user_res = await db.execute(select(Usuario).where(Usuario.id == payload.get("sub")))
    current_user = user_res.scalar_one_or_none()
    if not current_user or current_user.status != "activo":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )
    if current_user.tipo_usuario != "cliente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso exclusivo para clientes",
        )

    deadlines_query = (
        select(PlazoFatal)
        .options(selectinload(PlazoFatal.expediente))
        .join(Expediente)
        .where(
            Expediente.tenant_id == current_user.tenant_id,
            Expediente.cliente_principal_id == current_user.id,
            PlazoFatal.status == "pendiente"
        )
    )
    result = await db.execute(deadlines_query)
    deadlines = result.scalars().all()

    ical_content = CalendarService.generate_ical(
        deadlines,
        calendar_name="LexIntellectus - Mis Plazos Procesales"
    )

    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=lexintellectus_calendar.ics"
        }
    )
