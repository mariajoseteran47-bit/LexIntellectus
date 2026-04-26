"""Sprint 1: Multi-service architecture - expand all enums

Revision ID: a1b2c3d4e5f6
Revises: 1e4072f5b552
Create Date: 2026-04-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '1e4072f5b552'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════
    # 1. EXPAND service_type enum (add 4 new types)
    # ═══════════════════════════════════════════════════════
    op.execute("ALTER TYPE service_type ADD VALUE IF NOT EXISTS 'contrato'")
    op.execute("ALTER TYPE service_type ADD VALUE IF NOT EXISTS 'due_diligence'")
    op.execute("ALTER TYPE service_type ADD VALUE IF NOT EXISTS 'propiedad_intelectual'")
    op.execute("ALTER TYPE service_type ADD VALUE IF NOT EXISTS 'gestion_corporativa'")

    # ═══════════════════════════════════════════════════════
    # 2. EXPAND procedural_role enum (add notarial/contract/etc roles)
    # ═══════════════════════════════════════════════════════
    # Notarial
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'otorgante'")
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'adquiriente'")
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'compareciente'")
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'testigo_instrumental'")
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'interprete'")
    # Contracts / Mediation
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'parte_a'")
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'parte_b'")
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'mediador'")
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'arbitro'")
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'garante'")
    # Administrative
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'solicitante'")
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'beneficiario'")
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'gestor'")
    # Corporate
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'sociedad'")
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'socio_fundador'")
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'representante'")
    # Universal
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'cliente'")
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'contraparte'")
    op.execute("ALTER TYPE procedural_role ADD VALUE IF NOT EXISTS 'otro'")

    # ═══════════════════════════════════════════════════════
    # 3. EXPAND deadline_type enum
    # ═══════════════════════════════════════════════════════
    op.execute("ALTER TYPE deadline_type ADD VALUE IF NOT EXISTS 'registral'")
    op.execute("ALTER TYPE deadline_type ADD VALUE IF NOT EXISTS 'notarial'")
    op.execute("ALTER TYPE deadline_type ADD VALUE IF NOT EXISTS 'institucional'")

    # ═══════════════════════════════════════════════════════
    # 4. EXPAND event_type enum (add non-litigation types)
    # ═══════════════════════════════════════════════════════
    # Notarial
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'redaccion_borrador'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'revision_cliente'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'firma_escritura'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'presentacion_registro'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'inscripcion_completada'")
    # Contracts
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'redaccion_contrato'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'revision_contraparte'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'negociacion'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'firma_contrato'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'addendum'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'renovacion'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'terminacion'")
    # Administrative
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'presentacion_solicitud'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'requerimiento_institucion'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'subsanacion'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'resolucion_administrativa'")
    # Corporate
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'convocatoria'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'asamblea_realizada'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'acta_protocolizada'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'inscripcion_registral'")

    # ═══════════════════════════════════════════════════════
    # 5. ADD tipo_servicio column to workflow_stages table
    # ═══════════════════════════════════════════════════════
    # Create the new enum type first
    workflow_service_type = postgresql.ENUM(
        'litigio', 'escritura', 'asesoria', 'tramite', 'consulta',
        'mediacion', 'contrato', 'due_diligence',
        'propiedad_intelectual', 'gestion_corporativa',
        name='workflow_service_type',
        create_type=False
    )
    # Create the enum type in the database
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE workflow_service_type AS ENUM (
                'litigio', 'escritura', 'asesoria', 'tramite', 'consulta',
                'mediacion', 'contrato', 'due_diligence',
                'propiedad_intelectual', 'gestion_corporativa'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.add_column('workflow_stages',
        sa.Column('tipo_servicio', postgresql.ENUM(name='workflow_service_type', create_type=False), nullable=True)
    )

    # ═══════════════════════════════════════════════════════
    # 6. Make workflow_stages.ramo nullable (was NOT NULL)
    # ═══════════════════════════════════════════════════════
    op.alter_column('workflow_stages', 'ramo',
        existing_type=postgresql.ENUM(name='workflow_branch'),
        nullable=True
    )

    # ═══════════════════════════════════════════════════════
    # 7. Backfill: existing workflow_stages get tipo_servicio='litigio'
    # ═══════════════════════════════════════════════════════
    op.execute("UPDATE workflow_stages SET tipo_servicio = 'litigio' WHERE ramo IS NOT NULL AND tipo_servicio IS NULL")


def downgrade() -> None:
    # Remove the tipo_servicio column from workflow_stages
    op.drop_column('workflow_stages', 'tipo_servicio')

    # Make ramo NOT NULL again
    op.alter_column('workflow_stages', 'ramo',
        existing_type=postgresql.ENUM(name='workflow_branch'),
        nullable=False
    )

    # Note: PostgreSQL does not support removing values from enums.
    # The added enum values will remain but won't cause issues.
    op.execute("DROP TYPE IF EXISTS workflow_service_type")
