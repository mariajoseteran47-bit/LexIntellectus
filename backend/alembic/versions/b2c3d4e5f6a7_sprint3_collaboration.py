"""Sprint 3: Discussion threads and document approvals

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === Create enums ===
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE thread_channel_type AS ENUM ('interno', 'cliente');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE approval_status AS ENUM ('pendiente', 'aprobado', 'rechazado', 'revision');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    # === case_threads table ===
    op.create_table('case_threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('expediente_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('titulo', sa.String(300), nullable=False),
        sa.Column('tipo_canal', postgresql.ENUM('interno', 'cliente', name='thread_channel_type', create_type=False), nullable=False, server_default='interno'),
        sa.Column('cerrado', sa.Boolean(), server_default='false'),
        sa.Column('fijado', sa.Boolean(), server_default='false'),
        sa.Column('creado_por_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('total_mensajes', sa.Integer(), server_default='0'),
        sa.Column('ultimo_mensaje_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_case_threads_expediente', 'case_threads', ['expediente_id'])
    op.create_index('ix_case_threads_tenant', 'case_threads', ['tenant_id'])

    # === thread_messages table ===
    op.create_table('thread_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('hilo_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('case_threads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('autor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('contenido', sa.Text(), nullable=False),
        sa.Column('adjuntos', postgresql.JSONB(), server_default='[]'),
        sa.Column('menciones', postgresql.JSONB(), server_default='[]'),
        sa.Column('es_resolucion', sa.Boolean(), server_default='false'),
        sa.Column('editado', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_thread_messages_hilo', 'thread_messages', ['hilo_id'])

    # === document_approvals table ===
    op.create_table('document_approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('documento_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('expediente_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=True),
        sa.Column('solicitante_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('aprobador_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('estado', postgresql.ENUM('pendiente', 'aprobado', 'rechazado', 'revision', name='approval_status', create_type=False), nullable=False, server_default='pendiente'),
        sa.Column('motivo_solicitud', sa.Text(), nullable=True),
        sa.Column('comentarios_aprobador', sa.Text(), nullable=True),
        sa.Column('version_documento', sa.Integer(), server_default='1'),
        sa.Column('fecha_solicitud', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('fecha_respuesta', sa.DateTime(), nullable=True),
        sa.Column('fecha_limite', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_document_approvals_aprobador', 'document_approvals', ['aprobador_id'])
    op.create_index('ix_document_approvals_estado', 'document_approvals', ['estado'])
    op.create_index('ix_document_approvals_tenant', 'document_approvals', ['tenant_id'])


def downgrade() -> None:
    op.drop_table('document_approvals')
    op.drop_table('thread_messages')
    op.drop_table('case_threads')
    op.execute("DROP TYPE IF EXISTS approval_status")
    op.execute("DROP TYPE IF EXISTS thread_channel_type")
