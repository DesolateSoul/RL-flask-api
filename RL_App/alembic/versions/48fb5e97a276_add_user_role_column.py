"""add user role column

Revision ID: 48fb5e97a276
Revises: 
Create Date: 2025-06-12 11:50:08.350554

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48fb5e97a276'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('users',
                  sa.Column('role', sa.String(length=20),
                            server_default='user'))

    # Делаем первого пользователя администратором
    op.execute("UPDATE users SET role='admin' WHERE id=1")


def downgrade():
    op.drop_column('users', 'role')
