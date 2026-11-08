"""sprint6_public_api_webhooks

Revision ID: f6a7b8c9d0e1
Revises: e4f7df311641
Create Date: 2026-11-08 13:05:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e4f7df311641'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'api_keys',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('nombre', sa.String(length=120), nullable=False),
        sa.Column('plataforma', sa.String(length=50), nullable=False, server_default='custom'),
        sa.Column('key_prefix', sa.String(length=24), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('scopes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
    )
    op.create_index('ix_api_keys_tenant_id', 'api_keys', ['tenant_id'], unique=False)
    op.create_index('ix_api_keys_key_prefix', 'api_keys', ['key_prefix'], unique=False)
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)

    op.create_table(
        'webhook_subscriptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('nombre', sa.String(length=120), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('events', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('secret', sa.String(length=128), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhook_subscriptions_tenant_id', 'webhook_subscriptions', ['tenant_id'], unique=False)

    op.create_table(
        'webhook_delivery_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('subscription_id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.String(length=80), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('signature', sa.String(length=128), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('success', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['subscription_id'], ['webhook_subscriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhook_delivery_logs_tenant_id', 'webhook_delivery_logs', ['tenant_id'], unique=False)
    op.create_index('ix_webhook_delivery_logs_subscription_id', 'webhook_delivery_logs', ['subscription_id'], unique=False)

    op.create_table(
        'invoice_payments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('factura_id', sa.UUID(), nullable=False),
        sa.Column('monto', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('moneda', sa.String(length=3), nullable=False, server_default='NIO'),
        sa.Column('metodo_pago', sa.String(length=50), nullable=False, server_default='transferencia'),
        sa.Column('referencia_externa', sa.String(length=120), nullable=True),
        sa.Column('plataforma_origen', sa.String(length=50), nullable=False, server_default='manual'),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('fecha_pago', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['factura_id'], ['invoices.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_invoice_payments_tenant_id', 'invoice_payments', ['tenant_id'], unique=False)
    op.create_index('ix_invoice_payments_factura_id', 'invoice_payments', ['factura_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_invoice_payments_factura_id', table_name='invoice_payments')
    op.drop_index('ix_invoice_payments_tenant_id', table_name='invoice_payments')
    op.drop_table('invoice_payments')

    op.drop_index('ix_webhook_delivery_logs_subscription_id', table_name='webhook_delivery_logs')
    op.drop_index('ix_webhook_delivery_logs_tenant_id', table_name='webhook_delivery_logs')
    op.drop_table('webhook_delivery_logs')

    op.drop_index('ix_webhook_subscriptions_tenant_id', table_name='webhook_subscriptions')
    op.drop_table('webhook_subscriptions')

    op.drop_index('ix_api_keys_key_hash', table_name='api_keys')
    op.drop_index('ix_api_keys_key_prefix', table_name='api_keys')
    op.drop_index('ix_api_keys_tenant_id', table_name='api_keys')
    op.drop_table('api_keys')
