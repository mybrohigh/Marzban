"""Add user limits tables

Revision ID: b2f3f0a9c2ab
Revises: b1f3f0a9c2ab
Create Date: 2026-02-10 12:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2f3f0a9c2ab'
down_revision = 'b1f3f0a9c2ab'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Create user_limits table
    op.create_table(
        'user_limits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=32), nullable=False),
        sa.Column('limit_type', sa.String(length=50), nullable=False),
        sa.Column('limit_value', sa.BigInteger(), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=True, default='notify'),
        sa.Column('enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('notification_threshold', sa.Float(), nullable=True, default=0.8),
        sa.Column('webhook_url', sa.String(length=500), nullable=True),
        sa.Column('webhook_enabled', sa.Boolean(), nullable=True, default=False),
        sa.Column('auto_reset_enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('reset_schedule', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username', 'limit_type'),
        schema='users'
    )
    
    # ### Create limit_templates table
    op.create_table(
        'limit_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_by', sa.String(length=32), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='users'
    )
    
    # ### Create limit_violations table
    op.create_table(
        'limit_violations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=32), nullable=False),
        sa.Column('limit_type', sa.String(length=50), nullable=False),
        sa.Column('current_value', sa.BigInteger(), nullable=False),
        sa.Column('limit_value', sa.BigInteger(), nullable=False),
        sa.Column('violation_time', sa.DateTime(), nullable=False),
        sa.Column('action_taken', sa.String(length=20), nullable=False),
        sa.Column('resolved', sa.Boolean(), nullable=True, default=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), nullable=True, default=False),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='users'
    )
    
    # ### Create limit_notifications table
    op.create_table(
        'limit_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=32), nullable=False),
        sa.Column('limit_type', sa.String(length=50), nullable=False),
        sa.Column('notification_type', sa.String(length=20), nullable=False),  # email, telegram, webhook
        sa.Column('enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('threshold_percentage', sa.Float(), nullable=True, default=0.8),
        sa.Column('recipient', sa.String(length=500), nullable=True),  # email, chat_id, webhook_url
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='users'
    )
    
    # ### Create indexes for performance
    op.create_index('idx_user_limits_username', 'user_limits', ['username'])
    op.create_index('idx_user_limits_type', 'user_limits', ['limit_type'])
    op.create_index('idx_limit_violations_username', 'limit_violations', ['username'])
    op.create_index('idx_limit_violations_time', 'limit_violations', ['violation_time'])
    op.create_index('idx_limit_templates_name', 'limit_templates', ['name'])


def downgrade() -> None:
    # ### Drop user_limits table
    op.drop_table('limit_violations', schema='users')
    op.drop_table('limit_notifications', schema='users')
    op.drop_table('limit_templates', schema='users')
    op.drop_table('user_limits', schema='users')
