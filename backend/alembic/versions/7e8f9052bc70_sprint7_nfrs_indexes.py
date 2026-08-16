"""Sprint 7 NFRs indexes

Revision ID: 7e8f9052bc70
Revises: 6d9da041ab69
Create Date: 2026-05-31 12:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7e8f9052bc70'
down_revision = '6d9da041ab69'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Enable pg_trgm extension
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    
    # 2. GIN indexes for JSONB
    op.execute("CREATE INDEX IF NOT EXISTS ix_cases_co_abogados_gin ON cases USING GIN (co_abogados);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cases_datos_materia_gin ON cases USING GIN (datos_materia);")
    
    # 3. pg_trgm indexes for fuzzy search on cases
    op.execute("CREATE INDEX IF NOT EXISTS ix_cases_numero_causa_trgm ON cases USING GIN (numero_causa gin_trgm_ops);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cases_numero_interno_trgm ON cases USING GIN (numero_interno gin_trgm_ops);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cases_juzgado_trgm ON cases USING GIN (juzgado gin_trgm_ops);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cases_resumen_trgm ON cases USING GIN (resumen gin_trgm_ops);")

    # 4. Composite index for faster filtering
    op.execute("CREATE INDEX IF NOT EXISTS ix_cases_tenant_servicio ON cases (tenant_id, tipo_servicio);")

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_cases_tenant_servicio;")
    
    op.execute("DROP INDEX IF EXISTS ix_cases_resumen_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_cases_juzgado_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_cases_numero_interno_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_cases_numero_causa_trgm;")
    
    op.execute("DROP INDEX IF EXISTS ix_cases_datos_materia_gin;")
    op.execute("DROP INDEX IF EXISTS ix_cases_co_abogados_gin;")
    
    # Note: we usually don't drop the extension because other DBs might use it,
    # but for completeness:
    # op.execute("DROP EXTENSION IF EXISTS pg_trgm;")
