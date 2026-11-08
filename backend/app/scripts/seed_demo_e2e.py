"""
LexIntellectus ERP — End-to-End (E2E) Demo Data Seeder
Populates realistic Nicaraguan legal data across all 9 Sprints & 3 Dimensions:
1. Backoffice: 10 Legal Service Types, Deadlines, Workflow Tasks, Time Entries
2. Client Portal: Shared Documents, Client Discussion Threads, Approvals, Invoices (DGI/ALMA)
3. Integrations: Sample ERP API Keys (QuickBooks / Alegra), Webhook Subscriptions & Delivery Logs

Idempotent: Safe to run multiple times without duplicating demo records.
Usage:
    docker exec -e PYTHONPATH=. lexintellectus-api python app/scripts/seed_demo_e2e.py
"""

import asyncio
import hashlib
import secrets
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.billing import ContratoServicio, Factura, LineaFactura, RegistroTiempo
from app.models.case import EstadoExpediente, Expediente, ParteProcesal, PlazoFatal
from app.models.client import PerfilCliente
from app.models.collaboration import AprobacionDocumento, HiloDiscusion, MensajeHilo
from app.models.document import Documento
from app.models.integrations import ApiKey, PagoFactura, WebhookDeliveryLog, WebhookSubscription
from app.models.tenant import Despacho
from app.models.user import Usuario


DEMO_MATTERS = [
    {
        "numero_interno": "EXP-DEMO-001",
        "numero_causa": "00145-2026-CIV-MGA",
        "tipo_servicio": "litigio",
        "ramo": "civil",
        "materia_especifica": "Demanda Ejecutiva Mercantil por Pagaré",
        "juzgado": "Juzgado Tercero Distrito Civil Oral de Managua",
        "juez": "Dra. Claudia Esperanza Morales",
        "prioridad": "alta",
        "valor_estimado": Decimal("85000.00"),
        "resumen": "Ejecución de pagaré a la orden por suministro industrial incumplido.",
    },
    {
        "numero_interno": "EXP-DEMO-002",
        "numero_causa": "ESC-2026-042",
        "tipo_servicio": "escritura",
        "ramo": None,
        "materia_especifica": "Compraventa de Bien Inmueble e Hipoteca",
        "juzgado": "Protocolo Notarial No. 18 — Managua",
        "juez": None,
        "prioridad": "normal",
        "valor_estimado": Decimal("240000.00"),
        "resumen": "Otorgamiento de escritura pública de compraventa de nave logística en Carretera Norte.",
    },
    {
        "numero_interno": "EXP-DEMO-003",
        "numero_causa": "RET-2026-GC",
        "tipo_servicio": "asesoria",
        "ramo": "mercantil",
        "materia_especifica": "Iguala Corporativa y Laboral Mensual",
        "juzgado": None,
        "juez": None,
        "prioridad": "normal",
        "valor_estimado": Decimal("18000.00"),
        "resumen": "Asesoría jurídica preventiva continua en materia societaria, laboral y fiscal DGI/ALMA.",
    },
    {
        "numero_interno": "EXP-DEMO-004",
        "numero_causa": "MIFIC-2026-889",
        "tipo_servicio": "propiedad_intelectual",
        "ramo": "administrativo",
        "materia_especifica": "Registro de Marca Comercial y Nombre Industrial",
        "juzgado": "Registro de la Propiedad Intelectual (RPI - MIFIC)",
        "juez": None,
        "prioridad": "normal",
        "valor_estimado": Decimal("3500.00"),
        "resumen": "Inscripción multiclase (Clases 9, 35 y 42 de Niza) ante el MIFIC.",
    },
    {
        "numero_interno": "EXP-DEMO-005",
        "numero_causa": "DD-2026-ENERGIA",
        "tipo_servicio": "due_diligence",
        "ramo": "mercantil",
        "materia_especifica": "Auditoría Legal para Adquisición de Planta Solar",
        "juzgado": None,
        "juez": None,
        "prioridad": "urgente",
        "valor_estimado": Decimal("450000.00"),
        "resumen": "Revisión integral de concesiones MEM, permisos MARENA, contingencias laborales y títulos.",
    },
    {
        "numero_interno": "EXP-DEMO-006",
        "numero_causa": "CTR-2026-DIST",
        "tipo_servicio": "contrato",
        "ramo": "mercantil",
        "materia_especifica": "Contrato Marco de Distribución Exclusiva Centroamérica",
        "juzgado": None,
        "juez": None,
        "prioridad": "alta",
        "valor_estimado": Decimal("120000.00"),
        "resumen": "Negociación, redacción y cierre de contrato regional de distribución con cláusula arbitral.",
    },
    {
        "numero_interno": "EXP-DEMO-007",
        "numero_causa": "ARB-CAM-2026-09",
        "tipo_servicio": "mediacion",
        "ramo": "mercantil",
        "materia_especifica": "Arbitraje de Derecho por Liquidación de Obra Civil",
        "juzgado": "Centro de Mediación y Arbitraje de la Cámara de Comercio (CCSN)",
        "juez": "Tribunal Arbitral Colegiado",
        "prioridad": "alta",
        "valor_estimado": Decimal("175000.00"),
        "resumen": "Controversia sobre sobrecostos y prórrogas en contrato llave en mano.",
    },
    {
        "numero_interno": "EXP-DEMO-008",
        "numero_causa": "DGI-REC-2026-11",
        "tipo_servicio": "tramite",
        "ramo": "administrativo",
        "materia_especifica": "Recurso de Reposición y Revisión Fiscal DGI",
        "juzgado": "Dirección General de Ingresos (DGI) — Grandes Contribuyentes",
        "juez": None,
        "prioridad": "alta",
        "valor_estimado": Decimal("32000.00"),
        "resumen": "Impugnación administrativa de reparo fiscal sobre retenciones IR en la fuente.",
    },
    {
        "numero_interno": "EXP-DEMO-009",
        "numero_causa": "CORP-2026-AGA",
        "tipo_servicio": "gestion_corporativa",
        "ramo": "mercantil",
        "materia_especifica": "Asamblea General Extraordinaria y Reforma de Pacto Social",
        "juzgado": "Registro Público Mercantil de Managua",
        "juez": None,
        "prioridad": "normal",
        "valor_estimado": Decimal("6500.00"),
        "resumen": "Aumento de capital social, actualización de Beneficiario Final y elección de Junta Directiva.",
    },
    {
        "numero_interno": "EXP-DEMO-010",
        "numero_causa": "OP-2026-BANCA",
        "tipo_servicio": "consulta",
        "ramo": "mercantil",
        "materia_especifica": "Dictamen Legal sobre Fideicomiso de Garantía Sindicado",
        "juzgado": None,
        "juez": None,
        "prioridad": "normal",
        "valor_estimado": Decimal("4800.00"),
        "resumen": "Opinión legal vinculante sobre estructuración de garantías mobiliarias e inmobiliarias en Nicaragua.",
    },
]


async def seed_demo():
    print("🏛️  Iniciando carga de Datos Demo E2E para LexIntellectus...")
    default_pw_hash = hash_password("admin123")

    async with AsyncSessionLocal() as db:
        # 1. Locate or Create Primary Tenant & Admin User
        admin_res = await db.execute(
            select(Usuario).where(Usuario.email == "admin@lexintellectus.com")
        )
        admin = admin_res.scalar_one_or_none()

        if not admin:
            tenant = Despacho(
                id=uuid.uuid4(),
                nombre="Bufete LexIntellectus & Asociados",
                razon_social="LexIntellectus LegalTech S.A.",
                ruc="J0310000778899",
                email="contacto@lexintellectus.com",
                telefono="+505 2278-9000",
                direccion="Centro Ejecutivo Pellas, Piso 8, Managua",
                status="activo",
            )
            db.add(tenant)
            await db.flush()

            admin = Usuario(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email="admin@lexintellectus.com",
                password_hash=default_pw_hash,
                nombre="Carlos",
                apellido="Mendoza",
                tipo_usuario="admin_despacho",
                status="activo",
                mfa_enabled=False,
            )
            db.add(admin)
            await db.flush()
        else:
            tenant_res = await db.execute(
                select(Despacho).where(Despacho.id == admin.tenant_id)
            )
            tenant = tenant_res.scalar_one()

        tenant_id = tenant.id

        # 2. Locate or Create Primary Client User & CRM Profile
        client_res = await db.execute(
            select(Usuario).where(
                Usuario.email == "contacto@grupocentral.com.ni",
                Usuario.tenant_id == tenant_id,
            )
        )
        client_user = client_res.scalar_one_or_none()
        if not client_user:
            client_user = Usuario(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                email="contacto@grupocentral.com.ni",
                password_hash=default_pw_hash,
                nombre="Roberto",
                apellido="Chamorro (Grupo Central)",
                telefono="+505 8888-1122",
                tipo_usuario="cliente",
                status="activo",
                mfa_enabled=False,
            )
            db.add(client_user)
            await db.flush()

        profile_res = await db.execute(
            select(PerfilCliente).where(PerfilCliente.user_id == client_user.id)
        )
        client_profile = profile_res.scalar_one_or_none()
        if not client_profile:
            client_profile = PerfilCliente(
                id=uuid.uuid4(),
                user_id=client_user.id,
                tenant_id=tenant_id,
                tipo_persona="juridica",
                razon_social="Grupo Central de Inversiones S.A.",
                nombre_comercial="Grupo Central Nicaragua",
                ruc="J0310000184921",
                direccion_domicilio="Km 5.5 Carretera a Masaya, Edificio Corporativo, Managua",
                ciudad="Managua",
                departamento="Managua",
                pais="Nicaragua",
                segmento="corporativo",
                calificacion_riesgo="bajo",
                kyc_verificado=True,
                kyc_fecha_verificacion=date.today(),
                es_exento_iva=False,
                aplica_retenciones=True,
            )
            db.add(client_profile)
            await db.flush()

        # 3. Ensure Active Case Status exists
        status_res = await db.execute(
            select(EstadoExpediente).where(
                EstadoExpediente.tenant_id == tenant_id,
                EstadoExpediente.codigo == "activo",
            )
        )
        active_status = status_res.scalar_one_or_none()
        if not active_status:
            active_status = EstadoExpediente(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                codigo="activo",
                nombre="En Trámite",
                color_hex="#10B981",
                es_final=False,
                orden=1,
            )
            db.add(active_status)
            await db.flush()

        # 4. Seed All 10 Legal Service Matters
        created_cases = []
        for idx, m in enumerate(DEMO_MATTERS):
            existing_case = (
                await db.execute(
                    select(Expediente).where(
                        Expediente.tenant_id == tenant_id,
                        Expediente.numero_interno == m["numero_interno"],
                    )
                )
            ).scalar_one_or_none()

            if not existing_case:
                existing_case = Expediente(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    numero_interno=m["numero_interno"],
                    numero_causa=m["numero_causa"],
                    tipo_servicio=m["tipo_servicio"],
                    ramo=m["ramo"],
                    materia_especifica=m["materia_especifica"],
                    juzgado=m["juzgado"],
                    juez=m["juez"],
                    estado_id=active_status.id,
                    abogado_responsable_id=admin.id,
                    cliente_principal_id=client_user.id,
                    prioridad=m["prioridad"],
                    valor_estimado=m["valor_estimado"],
                    moneda="USD",
                    resumen=m["resumen"],
                    fecha_apertura=date.today() - timedelta(days=30 - idx * 2),
                )
                db.add(existing_case)
                await db.flush()

                party = ParteProcesal(
                    id=uuid.uuid4(),
                    expediente_id=existing_case.id,
                    nombre_completo="Grupo Central de Inversiones S.A.",
                    tipo_persona="juridica",
                    rol_procesal="demandante",
                    documento_identidad="J0310000184921",
                    representante_legal="Roberto Chamorro",
                )
                db.add(party)

            created_cases.append(existing_case)

        primary_case = created_cases[0]
        today = date.today()

        # 5. Seed Upcoming Deadlines (PlazoFatal)
        existing_dl = (
            await db.execute(
                select(PlazoFatal).where(PlazoFatal.expediente_id == primary_case.id)
            )
        ).scalars().all()
        if not existing_dl:
            deadlines_data = [
                (
                    "Audiencia Inicial y Evacuación de Pruebas (CPC)",
                    today + timedelta(days=2),
                    "09:30:00",
                    "critica",
                ),
                (
                    "Presentación de Escrito de Expresión de Agravios",
                    today + timedelta(days=5),
                    "14:00:00",
                    "alta",
                ),
                (
                    "Vencimiento de Inscripción Registral Mercantil",
                    today + timedelta(days=12),
                    "16:00:00",
                    "normal",
                ),
            ]
            for desc_text, due_date, due_hour, prio in deadlines_data:
                db.add(
                    PlazoFatal(
                        id=uuid.uuid4(),
                        expediente_id=primary_case.id,
                        descripcion=desc_text,
                        fecha_vencimiento=due_date,
                        hora_vencimiento=due_hour,
                        tipo_plazo="procesal",
                        prioridad=prio,
                        status="pendiente",
                        usuario_responsable_id=admin.id,
                    )
                )

        # 6. Seed Shared Documents, Approval & Client Discussion Thread
        existing_doc = (
            await db.execute(
                select(Documento).where(
                    Documento.tenant_id == tenant_id,
                    Documento.nombre_archivo == "Dictamen_Estrategico_Grupo_Central_2026.pdf",
                )
            )
        ).scalar_one_or_none()
        if not existing_doc:
            demo_doc = Documento(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                expediente_id=primary_case.id,
                nombre_archivo="Dictamen_Estrategico_Grupo_Central_2026.pdf",
                tipo_archivo="application/pdf",
                tamano_bytes=248500,
                storage_path=f"{tenant_id}/{primary_case.id}/dictamen_demo.pdf",
                subido_por_id=admin.id,
                descripcion="Dictamen ejecutivo y proyecto de liquidación para aprobación del cliente.",
                categoria="escrito_judicial",
                tipo_documento="dictamen",
                es_confidencial=False,
                tags=["dictamen", "portal", "ejecutivo"],
            )
            db.add(demo_doc)
            await db.flush()

            db.add(
                AprobacionDocumento(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    documento_id=demo_doc.id,
                    expediente_id=primary_case.id,
                    solicitante_id=admin.id,
                    aprobador_id=client_user.id,
                    estado="pendiente",
                    motivo_solicitud="Favor revisar y aprobar los montos de liquidación antes de presentar al Juzgado.",
                    fecha_limite=datetime.utcnow() + timedelta(days=3),
                )
            )

        existing_thread = (
            await db.execute(
                select(HiloDiscusion).where(
                    HiloDiscusion.expediente_id == primary_case.id,
                    HiloDiscusion.tipo_canal == "cliente",
                )
            )
        ).scalar_one_or_none()
        if not existing_thread:
            thread = HiloDiscusion(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                expediente_id=primary_case.id,
                titulo="Coordinación de Audiencia y Documentos de Respaldo",
                tipo_canal="cliente",
                creado_por_id=admin.id,
                fijado=True,
                total_mensajes=2,
                ultimo_mensaje_at=datetime.utcnow(),
            )
            db.add(thread)
            await db.flush()

            db.add_all(
                [
                    MensajeHilo(
                        id=uuid.uuid4(),
                        hilo_id=thread.id,
                        autor_id=admin.id,
                        contenido="Estimado don Roberto, hemos subido el Dictamen Estratégico al Portal del Cliente para su visto bueno.",
                    ),
                    MensajeHilo(
                        id=uuid.uuid4(),
                        hilo_id=thread.id,
                        autor_id=client_user.id,
                        contenido="Recibido Dr. Mendoza, nuestro comité financiero lo revisará hoy mismo y procederemos con la firma digital.",
                    ),
                ]
            )

        # 7. Seed Time Entries & Nicaraguan Invoices (Paid + Pending)
        inv_paid = (
            await db.execute(
                select(Factura).where(
                    Factura.tenant_id == tenant_id,
                    Factura.numero_factura == "FAC-DEMO-001",
                )
            )
        ).scalar_one_or_none()

        if not inv_paid:
            inv_paid = Factura(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                client_id=client_user.id,
                case_id=primary_case.id,
                numero_factura="FAC-DEMO-001",
                estado="pagada",
                fecha_emision=today - timedelta(days=20),
                fecha_vencimiento=today - timedelta(days=5),
                es_credito=True,
                dias_credito=15,
                subtotal=Decimal("2000.00"),
                iva_porcentaje=Decimal("15.00"),
                iva_monto=Decimal("300.00"),
                retencion_ir_porcentaje=Decimal("10.00"),
                retencion_ir_monto=Decimal("200.00"),
                retencion_alma_porcentaje=Decimal("1.50"),
                retencion_alma_monto=Decimal("30.00"),
                total_factura=Decimal("2300.00"),
                neto_a_pagar=Decimal("2070.00"),
                moneda="USD",
                sync_platform="alegra",
                sync_status="sincronizado",
                synced_at=datetime.utcnow() - timedelta(days=4),
                external_id="ALEGRA-NI-00841",
            )
            db.add(inv_paid)
            await db.flush()

            db.add(
                LineaFactura(
                    id=uuid.uuid4(),
                    factura_id=inv_paid.id,
                    descripcion="Honorarios Profesionales — Presentación de Demanda Ejecutiva y Embargo Preventivo",
                    cantidad=Decimal("1.00"),
                    precio_unitario=Decimal("2000.00"),
                    subtotal=Decimal("2000.00"),
                    tipo_item="honorario",
                    es_exento=False,
                )
            )
            db.add(
                PagoFactura(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    factura_id=inv_paid.id,
                    monto=Decimal("2070.00"),
                    moneda="USD",
                    metodo_pago="transferencia",
                    referencia_externa="BAC-ACH-904512",
                    plataforma_origen="alegra",
                    notas="Pago conciliado automáticamente vía API Pública",
                    fecha_pago=today - timedelta(days=4),
                )
            )

        inv_pending = (
            await db.execute(
                select(Factura).where(
                    Factura.tenant_id == tenant_id,
                    Factura.numero_factura == "FAC-DEMO-002",
                )
            )
        ).scalar_one_or_none()

        if not inv_pending:
            inv_pending = Factura(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                client_id=client_user.id,
                case_id=created_cases[4].id,  # Due Diligence
                numero_factura="FAC-DEMO-002",
                estado="enviada",
                fecha_emision=today - timedelta(days=2),
                fecha_vencimiento=today + timedelta(days=28),
                es_credito=True,
                dias_credito=30,
                subtotal=Decimal("3500.00"),
                iva_porcentaje=Decimal("15.00"),
                iva_monto=Decimal("450.00"),
                retencion_ir_porcentaje=Decimal("10.00"),
                retencion_ir_monto=Decimal("300.00"),
                retencion_alma_porcentaje=Decimal("1.50"),
                retencion_alma_monto=Decimal("45.00"),
                total_factura=Decimal("3950.00"),
                neto_a_pagar=Decimal("3605.00"),
                moneda="USD",
                sync_status="pendiente",
            )
            db.add(inv_pending)
            await db.flush()

            db.add_all(
                [
                    LineaFactura(
                        id=uuid.uuid4(),
                        factura_id=inv_pending.id,
                        descripcion="Honorarios por Due Diligence Legal y Regulatorio (Fase I)",
                        cantidad=Decimal("1.00"),
                        precio_unitario=Decimal("3000.00"),
                        subtotal=Decimal("3000.00"),
                        tipo_item="honorario",
                        es_exento=False,
                    ),
                    LineaFactura(
                        id=uuid.uuid4(),
                        factura_id=inv_pending.id,
                        descripcion="Aranceles Registrales y Certificaciones de Libertad de Gravamen (Exento IVA)",
                        cantidad=Decimal("1.00"),
                        precio_unitario=Decimal("500.00"),
                        subtotal=Decimal("500.00"),
                        tipo_item="gasto_registral",
                        es_exento=True,
                    ),
                ]
            )

            db.add_all(
                [
                    RegistroTiempo(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        case_id=primary_case.id,
                        user_id=admin.id,
                        horas=Decimal("6.50"),
                        descripcion="Redacción de escrito de oposición y preparación de pruebas documentales",
                        fecha_registro=today - timedelta(days=3),
                        tarifa_aplicada=Decimal("150.00"),
                        es_facturable=True,
                        facturado=False,
                    ),
                    RegistroTiempo(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        case_id=created_cases[4].id,
                        user_id=admin.id,
                        horas=Decimal("12.00"),
                        descripcion="Auditoría de títulos de propiedad y licencias ambientales MARENA",
                        fecha_registro=today - timedelta(days=1),
                        tarifa_aplicada=Decimal("180.00"),
                        es_facturable=True,
                        facturado=False,
                    ),
                ]
            )

        # 8. Seed Sample ERP API Key & Webhook Subscription (Sprint 6)
        demo_raw_key = "li_live_demo_alegra_erp_2026_nicaragua_sync_key"
        demo_key_hash = hashlib.sha256(demo_raw_key.encode("utf-8")).hexdigest()

        existing_key = (
            await db.execute(select(ApiKey).where(ApiKey.key_hash == demo_key_hash))
        ).scalar_one_or_none()

        if not existing_key:
            db.add(
                ApiKey(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    created_by=admin.id,
                    nombre="Conector Contable Alegra LATAM (Producción)",
                    plataforma="alegra",
                    key_prefix=demo_raw_key[:16],
                    key_hash=demo_key_hash,
                    scopes=[
                        "read:invoices",
                        "write:invoices",
                        "read:payments",
                        "write:payments",
                        "read:clients",
                        "read:matters",
                        "read:time_entries",
                    ],
                    rate_limit_per_minute=120,
                    activo=True,
                    last_used_at=datetime.utcnow(),
                )
            )

        existing_wh = (
            await db.execute(
                select(WebhookSubscription).where(
                    WebhookSubscription.tenant_id == tenant_id,
                    WebhookSubscription.nombre == "ERP Contable — Sincronización Automática",
                )
            )
        ).scalar_one_or_none()

        if not existing_wh:
            wh_sub = WebhookSubscription(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                created_by=admin.id,
                nombre="ERP Contable — Sincronización Automática",
                url="https://erp.grupocentral.com.ni/webhooks/lexintellectus",
                events=[
                    "matter.created",
                    "invoice.created",
                    "invoice.paid",
                    "payment.received",
                    "document.approved",
                ],
                secret=f"whsec_{secrets.token_hex(20)}",
                activo=True,
                failure_count=0,
                last_triggered_at=datetime.utcnow(),
            )
            db.add(wh_sub)
            await db.flush()

            db.add(
                WebhookDeliveryLog(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    subscription_id=wh_sub.id,
                    event_type="invoice.paid",
                    payload={
                        "event": "invoice.paid",
                        "numero_factura": "FAC-DEMO-001",
                        "neto_a_pagar": 2070.00,
                        "moneda": "USD",
                    },
                    signature="sha256=demo_hmac_signature_verified",
                    response_status=200,
                    response_body='{"status":"ok","erp":"alegra"}',
                    attempt_count=1,
                    success=True,
                    delivered_at=datetime.utcnow(),
                )
            )

        await db.commit()

        print("✅ Datos Demo E2E cargados exitosamente:")
        print("   • Backoffice Admin : admin@lexintellectus.com / admin123")
        print("   • Portal Cliente   : contacto@grupocentral.com.ni / admin123")
        print("   • API Key Demo ERP : li_live_demo_alegra_erp_2026_nicaragua_sync_key")
        print("   • 10 Expedientes (1 por cada tipo de servicio legal), Plazos, Hilos, Documentos y Facturas DGI/ALMA.")


if __name__ == "__main__":
    asyncio.run(seed_demo())
