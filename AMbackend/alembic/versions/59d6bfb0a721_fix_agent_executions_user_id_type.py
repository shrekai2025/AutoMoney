"""fix_agent_executions_user_id_type

Revision ID: 59d6bfb0a721
Revises: 003
Create Date: 2025-11-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59d6bfb0a721'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # 修改 user_id 列的类型从 UUID 到 Integer
    # PostgreSQL 需要显式转换，但由于当前列为空，可以直接改类型
    op.execute('ALTER TABLE agent_executions ALTER COLUMN user_id TYPE INTEGER USING NULL')

    # 添加外键约束
    op.create_foreign_key('fk_agent_executions_user_id', 'agent_executions', 'user', ['user_id'], ['id'])


def downgrade():
    # 删除外键约束
    op.drop_constraint('fk_agent_executions_user_id', 'agent_executions', type_='foreignkey')

    # 恢复 UUID 类型
    op.alter_column('agent_executions', 'user_id',
                    existing_type=sa.Integer(),
                    type_=sa.dialects.postgresql.UUID(),
                    existing_nullable=True)
