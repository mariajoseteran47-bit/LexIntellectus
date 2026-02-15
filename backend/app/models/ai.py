import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, DateTime, Numeric, Enum, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base

class LegalChunk(Base):
    __tablename__ = "legal_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(Enum('ley', 'decreto', 'jurisprudencia', 'doctrina', 'gaceta', name="ai_source_type"), nullable=False)
    source_id = Column(UUID(as_uuid=True), nullable=True) # Generic link to future source tables
    articulo_id = Column(UUID(as_uuid=True), nullable=True)
    
    chunk_index = Column(Integer)
    contenido_texto = Column(Text, nullable=False)
    contenido_markdown = Column(Text)
    
    # Embedding: 3072 dim for Gemini (as seen in runtime)
    vector_embedding = Column(Vector(3072))
    
    metadata_json = Column(JSONB)
    tokens_count = Column(Integer)
    hash_contenido = Column(String(64), unique=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LAASession(Base):
    __tablename__ = "laa_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)
    
    modo = Column(Enum('consultor', 'estratega', 'redactor', 'cartulario', name="ai_mode"), nullable=False)
    titulo = Column(String(255))
    contexto_documentos_ids = Column(ARRAY(UUID(as_uuid=True)))
    
    tokens_consumidos = Column(Integer, default=0)
    costo_estimado_usd = Column(Numeric(10, 4), default=0)
    status = Column(Enum('activa', 'cerrada', 'archivada', name="session_status"), default='activa')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("LAAMessage", back_populates="session", cascade="all, delete-orphan")
    usuario = relationship("Usuario")
    expediente = relationship("Expediente")

class LAAMessage(Base):
    __tablename__ = "laa_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("laa_sessions.id"), nullable=False)
    
    rol = Column(Enum('user', 'assistant', 'system', 'tool', name="message_role"), nullable=False)
    contenido = Column(Text)
    contenido_markdown = Column(Text)
    
    attachments_json = Column(JSONB)
    chunks_utilizados_ids = Column(ARRAY(UUID(as_uuid=True)))
    articulos_citados_ids = Column(ARRAY(UUID(as_uuid=True)))
    jurisprudencia_citada_ids = Column(ARRAY(UUID(as_uuid=True)))
    
    tokens_prompt = Column(Integer)
    tokens_completion = Column(Integer)
    modelo_usado = Column(String(50))
    latencia_ms = Column(Integer)
    
    feedback_rating = Column(Integer)
    feedback_comment = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("LAASession", back_populates="messages")

class LAACaseTheory(Base):
    __tablename__ = "laa_case_theories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("laa_sessions.id"))
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"))
    version = Column(Integer, default=1)
    
    resumen_ejecutivo = Column(Text)
    hechos_facticos_json = Column(JSONB)
    fundamento_juridico_json = Column(JSONB)
    pruebas_json = Column(JSONB)
    fortalezas = Column(ARRAY(Text))
    debilidades = Column(ARRAY(Text))
    estrategia_recomendada = Column(Text)
    proximos_pasos = Column(ARRAY(Text))
    
    confianza_score = Column(Numeric(3, 2))
    aprobada_por = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    fecha_aprobacion = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class LAAValidation(Base):
    __tablename__ = "laa_notarial_validations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("laa_sessions.id"))
    documento_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    
    resultado_global = Column(Enum('aprobado', 'con_advertencias', 'bloqueado', name="validation_result"))
    validaciones_json = Column(JSONB)
    errores_count = Column(Integer)
    advertencias_count = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
