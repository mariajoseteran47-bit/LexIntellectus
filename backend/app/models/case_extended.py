"""
LexIntellectus — Modelos Extendidos de Gestión de Expedientes
Actuaciones procesales, notas internas, historial de estados, y teoría del caso.
Diseñado para litigantes que necesitan gestionar casos reales en TODAS las materias.
"""

import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Date, DateTime,
    ForeignKey, Enum, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class EtapaProcesal(Base):
    """
    Etapas procesales configurables por ramo jurídico.
    Cada ramo tiene su propio flujo procesal:
        Civil: Demanda → Emplazamiento → Contestación → Pruebas → Sentencia
        Penal: Denuncia → Investigación → Audiencia Preliminar → Juicio Oral → Sentencia
        Familia: Solicitud → Mediación → Audiencia → Sentencia
    """
    __tablename__ = "workflow_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    ramo = Column(
        Enum(
            'civil', 'penal', 'familia', 'laboral', 'mercantil',
            'constitucional', 'sucesiones', 'administrativo', 'notarial',
            name="workflow_branch"
        ),
        nullable=False
    )
    tipo_proceso = Column(String(100))  # ordinario, ejecutivo, divorcio_contencioso...
    codigo = Column(String(50), nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    orden = Column(Integer, default=0)
    dias_plazo_legal = Column(Integer)
    tipo_dias = Column(Enum('habiles', 'calendario', name="stage_days_type"), default='habiles')
    base_legal = Column(String(200))
    es_final = Column(Boolean, default=False)
    acciones_requeridas = Column(JSONB)
    plantillas_sugeridas = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow)


class ActuacionProcesal(Base):
    """
    Cada acción/evento que ocurre en un caso.
    Es el CORAZÓN del seguimiento — registra la vida del expediente.
    Desde la presentación de la demanda hasta la sentencia firme.
    """
    __tablename__ = "case_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)

    # Clasificación
    tipo = Column(
        Enum(
            'escrito_presentado',      # Escrito que NOSOTROS presentamos
            'escrito_contraparte',     # Escrito de la contraparte
            'providencia',             # Resolución del juez (no sentencia)
            'auto',                    # Auto judicial
            'sentencia',               # Sentencia (parcial o definitiva)
            'audiencia',               # Comparecencia programada o realizada
            'notificacion_judicial',   # Notificación del juzgado
            'recurso_interpuesto',     # Recurso que interponemos
            'recurso_contraparte',     # Recurso de la contraparte
            'incidente',               # Incidente procesal
            'excepcion',               # Excepción opuesta
            'medida_cautelar',         # Solicitud o ejecución de medida
            'diligencia',              # Inspección, embargo, reconocimiento
            'prueba_admitida',         # Prueba admitida por el juez
            'prueba_evacuada',         # Prueba practicada/evacuada
            'acuerdo',                 # Conciliación, mediación, transacción
            'peritaje',                # Dictamen pericial
            'nota_interna',            # Nota del equipo (no procesal)
            'otro',
            name="event_type"
        ),
        nullable=False
    )

    titulo = Column(String(300), nullable=False)
    descripcion = Column(Text)
    fecha_evento = Column(DateTime, nullable=False)
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    # Contexto procesal
    etapa_procesal_id = Column(UUID(as_uuid=True), ForeignKey("workflow_stages.id"), nullable=True)
    resultado = Column(Text)
    base_legal = Column(String(200))

    # Vinculaciones
    documento_ids = Column(JSONB, default=[])
    plazo_generado_id = Column(UUID(as_uuid=True), ForeignKey("deadlines.id"), nullable=True)

    # Responsabilidad
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    asignado_a_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Estado de la actuación
    estado = Column(
        Enum('pendiente', 'completado', 'vencido', 'cancelado', name="event_status"),
        default='completado'
    )

    # IA
    analisis_ia = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    expediente = relationship("Expediente", backref="actuaciones")
    etapa = relationship("EtapaProcesal")
    registrado_por = relationship("Usuario", foreign_keys=[registrado_por_id])
    asignado_a = relationship("Usuario", foreign_keys=[asignado_a_id])


class NotaInterna(Base):
    """
    Notas internas del equipo legal.
    NO son parte del expediente judicial — son estrategia interna.
    Ej: "El testigo X se contradijo en la declaración del folio 45"
    """
    __tablename__ = "case_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)

    tipo = Column(
        Enum(
            'estrategia',         # Análisis estratégico
            'investigacion',      # Hallazgo de investigación
            'recordatorio',       # Algo que no olvidar
            'reunion_cliente',    # Minuta con el cliente
            'reunion_equipo',     # Minuta interna
            'observacion',        # Observación general
            'contraargumento',    # Cómo respondería la contraparte
            'jurisprudencia',     # Jurisprudencia encontrada
            name="note_type"
        ),
        default='observacion'
    )

    contenido = Column(Text, nullable=False)
    es_privada = Column(Boolean, default=False)
    prioridad = Column(
        Enum('normal', 'importante', 'urgente', name="note_priority"),
        default='normal'
    )

    autor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    expediente = relationship("Expediente", backref="notas")
    autor = relationship("Usuario")


class HistorialEstado(Base):
    """
    Registro de cada transición de estado de un expediente.
    Nunca se borra — es el registro de auditoría del flujo procesal.
    """
    __tablename__ = "case_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    estado_anterior_id = Column(UUID(as_uuid=True), ForeignKey("case_statuses.id"), nullable=True)
    estado_nuevo_id = Column(UUID(as_uuid=True), ForeignKey("case_statuses.id"), nullable=False)
    etapa_procesal_id = Column(UUID(as_uuid=True), ForeignKey("workflow_stages.id"), nullable=True)
    motivo = Column(Text)
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    expediente = relationship("Expediente", backref="historial_estados")
    estado_anterior = relationship("EstadoExpediente", foreign_keys=[estado_anterior_id])
    estado_nuevo = relationship("EstadoExpediente", foreign_keys=[estado_nuevo_id])
    registrado_por = relationship("Usuario")


class TeoriaCaso(Base):
    """
    Estructura formal de la teoría del caso.
    Las 3 columnas del litigio: HECHOS → DERECHO → PRUEBA
    Más: estrategia, fortalezas, debilidades, contraargumentos.
    """
    __tablename__ = "case_theories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)

    # --- TEORÍA FÁCTICA ---
    # [{orden, hecho, fecha, es_controvertido, probado}]
    hechos_relevantes = Column(JSONB, default=[])

    # --- TEORÍA JURÍDICA ---
    # [{pretension, base_legal, fundamentacion}]
    pretensiones = Column(JSONB, default=[])
    # [{norma, articulo, texto_relevante, aplicacion}]
    normas_aplicables = Column(JSONB, default=[])
    # [{excepcion, tipo, respuesta_preparada}]
    excepciones_previstas = Column(JSONB, default=[])

    # --- TEORÍA PROBATORIA ---
    # [{tipo, descripcion, hecho_que_prueba, estado, observaciones}]
    pruebas_plan = Column(JSONB, default=[])

    # --- ESTRATEGIA ---
    fortalezas = Column(Text)
    debilidades = Column(Text)
    riesgos = Column(Text)
    estrategia_general = Column(Text)
    # [{argumento_contraparte, nuestra_respuesta}]
    contraargumentos = Column(JSONB, default=[])

    # Metadata
    generada_por_ia = Column(Boolean, default=False)
    analisis_ia = Column(Text)
    version = Column(Integer, default=1)
    autor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    expediente = relationship("Expediente", backref="teorias")
    autor = relationship("Usuario")
