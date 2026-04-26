"""
LexIntellectus — Seed: Workflow Stages for ALL Service Types
Sprint 1, Task 1.9
Creates workflow stages for each of the 10 service types.
Run with: python -m app.scripts.seed_workflow_stages
"""

import asyncio
import uuid
from sqlalchemy import select, text
from app.core.database import engine as async_engine, AsyncSessionLocal as AsyncSessionFactory
from app.models.case_extended import EtapaProcesal
from app.models.tenant import Despacho


# ═══════════════════════════════════════════════════════════════
# WORKFLOW DEFINITIONS FOR ALL 10 SERVICE TYPES
# ═══════════════════════════════════════════════════════════════

WORKFLOW_STAGES = {
    # ─── ESCRITURA NOTARIAL ───
    "escritura": [
        {"codigo": "ESC-01", "nombre": "Solicitud del Cliente", "orden": 1, "dias_plazo_legal": 1,
         "descripcion": "El cliente solicita la elaboración de la escritura. Se recopilan datos iniciales."},
        {"codigo": "ESC-02", "nombre": "Recopilación de Documentos", "orden": 2, "dias_plazo_legal": 5,
         "descripcion": "Recopilar cédulas, certificados registrales, solvencias, avalúos, etc."},
        {"codigo": "ESC-03", "nombre": "Redacción del Borrador", "orden": 3, "dias_plazo_legal": 3,
         "descripcion": "El notario redacta el borrador de la escritura pública."},
        {"codigo": "ESC-04", "nombre": "Revisión del Cliente", "orden": 4, "dias_plazo_legal": 3,
         "descripcion": "El cliente revisa el borrador y solicita correcciones si es necesario."},
        {"codigo": "ESC-05", "nombre": "Firma y Autorización", "orden": 5, "dias_plazo_legal": 2,
         "descripcion": "Comparecencia de las partes para firma. El notario autoriza la escritura."},
        {"codigo": "ESC-06", "nombre": "Inscripción Registral", "orden": 6, "dias_plazo_legal": 30,
         "descripcion": "Presentación ante el Registro Público para su inscripción."},
        {"codigo": "ESC-07", "nombre": "Entrega al Cliente", "orden": 7, "dias_plazo_legal": 2, "es_final": True,
         "descripcion": "Entrega del testimonio inscrito y certificaciones al cliente."},
    ],

    # ─── ASESORÍA LEGAL CONTINUA ───
    "asesoria": [
        {"codigo": "ASE-01", "nombre": "Propuesta de Servicios", "orden": 1, "dias_plazo_legal": 3,
         "descripcion": "Elaboración y presentación de propuesta de iguala/retainer."},
        {"codigo": "ASE-02", "nombre": "Negociación de Términos", "orden": 2, "dias_plazo_legal": 5,
         "descripcion": "Negociación de alcance, horas incluidas, tarifa y período."},
        {"codigo": "ASE-03", "nombre": "Firma del Contrato", "orden": 3, "dias_plazo_legal": 2,
         "descripcion": "Firma del contrato de iguala o retainer."},
        {"codigo": "ASE-04", "nombre": "Vigencia Activa", "orden": 4, "dias_plazo_legal": None,
         "descripcion": "Período de vigencia del contrato. Se atienden consultas y se generan reportes."},
        {"codigo": "ASE-05", "nombre": "Reporte Periódico", "orden": 5, "dias_plazo_legal": 30,
         "descripcion": "Generación de reporte mensual de horas consumidas y consultas atendidas."},
        {"codigo": "ASE-06", "nombre": "Renovación o Cierre", "orden": 6, "dias_plazo_legal": 15, "es_final": True,
         "descripcion": "Evaluación para renovación del contrato o cierre formal."},
    ],

    # ─── TRÁMITE ADMINISTRATIVO ───
    "tramite": [
        {"codigo": "TRA-01", "nombre": "Solicitud del Trámite", "orden": 1, "dias_plazo_legal": 1,
         "descripcion": "El cliente solicita la gestión. Se identifica la institución y requisitos."},
        {"codigo": "TRA-02", "nombre": "Preparación Documental", "orden": 2, "dias_plazo_legal": 5,
         "descripcion": "Recopilación y preparación de todos los documentos requeridos."},
        {"codigo": "TRA-03", "nombre": "Presentación ante Institución", "orden": 3, "dias_plazo_legal": 2,
         "descripcion": "Presentación formal de la solicitud ante la institución correspondiente."},
        {"codigo": "TRA-04", "nombre": "Seguimiento Institucional", "orden": 4, "dias_plazo_legal": None,
         "descripcion": "Seguimiento del estado del trámite. Atención de requerimientos adicionales."},
        {"codigo": "TRA-05", "nombre": "Resolución", "orden": 5, "dias_plazo_legal": None,
         "descripcion": "La institución emite resolución (aprobación, denegación, observaciones)."},
        {"codigo": "TRA-06", "nombre": "Entrega al Cliente", "orden": 6, "dias_plazo_legal": 2, "es_final": True,
         "descripcion": "Entrega del documento o certificación obtenida al cliente."},
    ],

    # ─── CONSULTA PUNTUAL ───
    "consulta": [
        {"codigo": "CON-01", "nombre": "Solicitud de Consulta", "orden": 1, "dias_plazo_legal": 1,
         "descripcion": "El cliente solicita una consulta. Se define área y modalidad."},
        {"codigo": "CON-02", "nombre": "Agendamiento", "orden": 2, "dias_plazo_legal": 2,
         "descripcion": "Se agenda la cita (presencial, virtual o escrita)."},
        {"codigo": "CON-03", "nombre": "Consulta Realizada", "orden": 3, "dias_plazo_legal": 1,
         "descripcion": "Se realiza la consulta. Se toman notas y se identifican acciones."},
        {"codigo": "CON-04", "nombre": "Opinión Legal Formal", "orden": 4, "dias_plazo_legal": 5,
         "descripcion": "Si fue solicitada, se elabora opinión legal escrita."},
        {"codigo": "CON-05", "nombre": "Cierre y Facturación", "orden": 5, "dias_plazo_legal": 2, "es_final": True,
         "descripcion": "Se cierra la consulta y se emite factura."},
    ],

    # ─── MEDIACIÓN / ARBITRAJE ───
    "mediacion": [
        {"codigo": "MED-01", "nombre": "Solicitud de Mediación", "orden": 1, "dias_plazo_legal": 3,
         "descripcion": "Se solicita la mediación/arbitraje. Se identifica la cláusula compromisoria."},
        {"codigo": "MED-02", "nombre": "Designación de Mediador/Árbitro", "orden": 2, "dias_plazo_legal": 10,
         "descripcion": "Se designa al mediador o árbitro según el procedimiento aplicable."},
        {"codigo": "MED-03", "nombre": "Sesiones de Mediación", "orden": 3, "dias_plazo_legal": None,
         "descripcion": "Se llevan a cabo las sesiones de mediación o audiencias arbitrales."},
        {"codigo": "MED-04", "nombre": "Acuerdo o Laudo", "orden": 4, "dias_plazo_legal": 15,
         "descripcion": "Se alcanza acuerdo de mediación o se emite laudo arbitral."},
        {"codigo": "MED-05", "nombre": "Registro y Cierre", "orden": 5, "dias_plazo_legal": 5, "es_final": True,
         "descripcion": "Se registra el acuerdo/laudo ante autoridades si aplica. Cierre del caso."},
    ],

    # ─── ADMINISTRACIÓN DE CONTRATOS ───
    "contrato": [
        {"codigo": "CTR-01", "nombre": "Solicitud de Contrato", "orden": 1, "dias_plazo_legal": 1,
         "descripcion": "El cliente solicita redacción, revisión o negociación de un contrato."},
        {"codigo": "CTR-02", "nombre": "Redacción del Borrador", "orden": 2, "dias_plazo_legal": 5,
         "descripcion": "Se redacta la primera versión del contrato."},
        {"codigo": "CTR-03", "nombre": "Revisión Interna", "orden": 3, "dias_plazo_legal": 2,
         "descripcion": "Revisión interna por el equipo legal antes de enviar al cliente."},
        {"codigo": "CTR-04", "nombre": "Negociación con Contraparte", "orden": 4, "dias_plazo_legal": None,
         "descripcion": "Intercambio de versiones y negociación de cláusulas con la contraparte."},
        {"codigo": "CTR-05", "nombre": "Versión Final", "orden": 5, "dias_plazo_legal": 3,
         "descripcion": "Se acuerda la versión final del contrato."},
        {"codigo": "CTR-06", "nombre": "Firma del Contrato", "orden": 6, "dias_plazo_legal": 5,
         "descripcion": "Las partes firman el contrato. Se digitaliza y almacena."},
        {"codigo": "CTR-07", "nombre": "Vigencia y Seguimiento", "orden": 7, "dias_plazo_legal": None,
         "descripcion": "Seguimiento de hitos contractuales, alertas de vencimiento y renovación."},
        {"codigo": "CTR-08", "nombre": "Vencimiento o Terminación", "orden": 8, "dias_plazo_legal": 30, "es_final": True,
         "descripcion": "El contrato vence, se renueva o se termina."},
    ],

    # ─── DUE DILIGENCE ───
    "due_diligence": [
        {"codigo": "DD-01", "nombre": "Solicitud de Due Diligence", "orden": 1, "dias_plazo_legal": 1,
         "descripcion": "El cliente solicita la investigación. Se define el objeto y alcance."},
        {"codigo": "DD-02", "nombre": "Definición de Alcance", "orden": 2, "dias_plazo_legal": 3,
         "descripcion": "Se acuerdan áreas a investigar, plazos y equipo asignado."},
        {"codigo": "DD-03", "nombre": "Configuración de Data Room", "orden": 3, "dias_plazo_legal": 5,
         "descripcion": "Se solicitan documentos y se configura el repositorio de información."},
        {"codigo": "DD-04", "nombre": "Revisión Documental", "orden": 4, "dias_plazo_legal": None,
         "descripcion": "Análisis exhaustivo de documentos recibidos. Se identifican hallazgos."},
        {"codigo": "DD-05", "nombre": "Reporte de Hallazgos", "orden": 5, "dias_plazo_legal": 5,
         "descripcion": "Se elabora el reporte con hallazgos, riesgos y recomendaciones."},
        {"codigo": "DD-06", "nombre": "Presentación y Cierre", "orden": 6, "dias_plazo_legal": 3, "es_final": True,
         "descripcion": "Se presenta el informe ejecutivo al cliente. Cierre del proyecto."},
    ],

    # ─── PROPIEDAD INTELECTUAL ───
    "propiedad_intelectual": [
        {"codigo": "PI-01", "nombre": "Búsqueda de Antecedentes", "orden": 1, "dias_plazo_legal": 5,
         "descripcion": "Búsqueda en bases de datos de marcas/patentes existentes."},
        {"codigo": "PI-02", "nombre": "Preparación de Solicitud", "orden": 2, "dias_plazo_legal": 5,
         "descripcion": "Preparación de la solicitud de registro con toda la documentación."},
        {"codigo": "PI-03", "nombre": "Presentación ante MIFIC", "orden": 3, "dias_plazo_legal": 2,
         "descripcion": "Presentación de la solicitud ante la autoridad competente."},
        {"codigo": "PI-04", "nombre": "Examen de Forma", "orden": 4, "dias_plazo_legal": 15,
         "descripcion": "La autoridad revisa que la solicitud cumpla requisitos formales."},
        {"codigo": "PI-05", "nombre": "Publicación en Gaceta", "orden": 5, "dias_plazo_legal": 60,
         "descripcion": "Publicación para que terceros puedan presentar oposición."},
        {"codigo": "PI-06", "nombre": "Período de Oposición", "orden": 6, "dias_plazo_legal": 60,
         "descripcion": "Plazo para que terceros presenten oposición. Se defiende si es necesario."},
        {"codigo": "PI-07", "nombre": "Registro Otorgado", "orden": 7, "dias_plazo_legal": 30, "es_final": True,
         "descripcion": "La autoridad otorga el registro. Se entrega certificado al cliente."},
    ],

    # ─── GESTIÓN CORPORATIVA ───
    "gestion_corporativa": [
        {"codigo": "GC-01", "nombre": "Solicitud del Acto Corporativo", "orden": 1, "dias_plazo_legal": 1,
         "descripcion": "El cliente solicita un acto corporativo (reforma, actualización de junta, etc.)."},
        {"codigo": "GC-02", "nombre": "Preparación de Convocatoria", "orden": 2, "dias_plazo_legal": 3,
         "descripcion": "Se redacta la convocatoria según el pacto social y la ley."},
        {"codigo": "GC-03", "nombre": "Convocatoria Publicada", "orden": 3, "dias_plazo_legal": 15,
         "descripcion": "Se publica/notifica la convocatoria con la anticipación legal requerida."},
        {"codigo": "GC-04", "nombre": "Asamblea / Junta Realizada", "orden": 4, "dias_plazo_legal": 1,
         "descripcion": "Se celebra la asamblea de accionistas o junta directiva."},
        {"codigo": "GC-05", "nombre": "Acta Protocolizada", "orden": 5, "dias_plazo_legal": 5,
         "descripcion": "El acta se protocoliza ante notario público."},
        {"codigo": "GC-06", "nombre": "Inscripción en Registro Mercantil", "orden": 6, "dias_plazo_legal": 30,
         "descripcion": "Se presenta la escritura ante el Registro Público Mercantil."},
        {"codigo": "GC-07", "nombre": "Actualización Completada", "orden": 7, "dias_plazo_legal": 2, "es_final": True,
         "descripcion": "Inscripción confirmada. Se actualizan los documentos corporativos del cliente."},
    ],
}


async def seed_workflow_stages():
    """Seed workflow stages for all service types for every tenant."""
    async with AsyncSessionFactory() as session:
        # Get all tenants
        result = await session.execute(select(Despacho))
        tenants = result.scalars().all()

        if not tenants:
            print("❌ No tenants found. Please create a tenant first.")
            return

        for tenant in tenants:
            print(f"\n🏛️  Tenant: {tenant.nombre} ({tenant.id})")

            for tipo_servicio, stages in WORKFLOW_STAGES.items():
                # Check if stages already exist for this tenant + service type
                existing = await session.execute(
                    select(EtapaProcesal).where(
                        EtapaProcesal.tenant_id == tenant.id,
                        EtapaProcesal.tipo_servicio == tipo_servicio
                    )
                )
                if existing.scalars().first():
                    print(f"   ⏭️  {tipo_servicio}: ya tiene etapas, omitiendo")
                    continue

                for stage_data in stages:
                    stage = EtapaProcesal(
                        id=uuid.uuid4(),
                        tenant_id=tenant.id,
                        ramo=None,  # Non-litigation services don't use ramo
                        tipo_servicio=tipo_servicio,
                        tipo_proceso=None,
                        codigo=stage_data["codigo"],
                        nombre=stage_data["nombre"],
                        descripcion=stage_data.get("descripcion", ""),
                        orden=stage_data["orden"],
                        dias_plazo_legal=stage_data.get("dias_plazo_legal"),
                        es_final=stage_data.get("es_final", False),
                    )
                    session.add(stage)

                print(f"   ✅ {tipo_servicio}: {len(stages)} etapas creadas")

        await session.commit()
        print("\n🎉 Seed de workflow stages completado.")


if __name__ == "__main__":
    asyncio.run(seed_workflow_stages())
