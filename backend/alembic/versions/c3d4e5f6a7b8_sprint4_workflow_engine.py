"""Sprint 4: Workflow templates, tasks, checklist, conflict check

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === Create enums ===
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE task_status AS ENUM ('pendiente', 'en_progreso', 'completada', 'cancelada');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE task_category AS ENUM ('procesal', 'documental', 'administrativa', 'cliente', 'interna');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    # === Enable pg_trgm for fuzzy search ===
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # === workflow_templates table ===
    op.create_table('workflow_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('tipo_servicio', sa.String(50), nullable=False),
        sa.Column('ramo', sa.String(50), nullable=True),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('tareas', postgresql.JSONB(), server_default='[]'),
        sa.Column('docs_requeridos', postgresql.JSONB(), server_default='[]'),
        sa.Column('reglas_transicion', postgresql.JSONB(), server_default='[]'),
        sa.Column('activo', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # === case_tasks table ===
    op.create_table('case_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('expediente_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('titulo', sa.String(300), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('estado', postgresql.ENUM('pendiente', 'en_progreso', 'completada', 'cancelada', name='task_status', create_type=False), nullable=False, server_default='pendiente'),
        sa.Column('categoria', postgresql.ENUM('procesal', 'documental', 'administrativa', 'cliente', 'interna', name='task_category', create_type=False), nullable=False, server_default='administrativa'),
        sa.Column('obligatoria', sa.Boolean(), server_default='false'),
        sa.Column('asignado_a_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('fecha_limite', sa.DateTime(), nullable=True),
        sa.Column('fecha_completada', sa.DateTime(), nullable=True),
        sa.Column('orden', sa.Integer(), server_default='0'),
        sa.Column('etapa_codigo', sa.String(50), nullable=True),
        sa.Column('plantilla_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workflow_templates.id'), nullable=True),
        sa.Column('creado_por_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_case_tasks_expediente', 'case_tasks', ['expediente_id'])
    op.create_index('ix_case_tasks_estado', 'case_tasks', ['estado'])

    # === case_doc_checklist table ===
    op.create_table('case_doc_checklist',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('expediente_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=False),
        sa.Column('nombre_documento', sa.String(300), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('obligatorio', sa.Boolean(), server_default='true'),
        sa.Column('etapa_codigo', sa.String(50), nullable=True),
        sa.Column('recibido', sa.Boolean(), server_default='false'),
        sa.Column('documento_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=True),
        sa.Column('fecha_recibido', sa.DateTime(), nullable=True),
        sa.Column('verificado_por_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_case_doc_checklist_expediente', 'case_doc_checklist', ['expediente_id'])

    # === conflict_check_results table ===
    op.create_table('conflict_check_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('expediente_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cases.id'), nullable=True),
        sa.Column('nombre_buscado', sa.String(300), nullable=False),
        sa.Column('documento_buscado', sa.String(50), nullable=True),
        sa.Column('tiene_conflicto', sa.Boolean(), server_default='false'),
        sa.Column('coincidencias', postgresql.JSONB(), server_default='[]'),
        sa.Column('verificado_por_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('resolucion', sa.Text(), nullable=True),
        sa.Column('aprobado', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # === Trigram indexes for fuzzy search ===
    op.execute("CREATE INDEX IF NOT EXISTS ix_case_parties_nombre_trgm ON case_parties USING gin (nombre_completo gin_trgm_ops);")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_case_parties_nombre_trgm;")
    op.drop_table('conflict_check_results')
    op.drop_table('case_doc_checklist')
    op.drop_table('case_tasks')
    op.drop_table('workflow_templates')
    op.execute("DROP TYPE IF EXISTS task_category")
    op.execute("DROP TYPE IF EXISTS task_status")
