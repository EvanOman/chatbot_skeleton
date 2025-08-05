"""add client_msg_id for deduplication

Revision ID: b2c3d4e5f6g7
Revises: 41598cbf6b2a
Create Date: 2025-07-29 03:02:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: str | Sequence[str] | None = "41598cbf6b2a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add client_msg_id column for message deduplication."""
    # Add client_msg_id column to chat_message table
    op.add_column(
        "chat_message",
        sa.Column("client_msg_id", sa.String(length=255), nullable=True)
    )
    
    # Add unique index on client_msg_id for deduplication
    # Only non-null values should be unique (allows multiple NULL values)
    op.create_index(
        "idx_chat_message_client_msg_id_unique",
        "chat_message",
        ["client_msg_id"],
        unique=True,
        postgresql_where=sa.text("client_msg_id IS NOT NULL")
    )


def downgrade() -> None:
    """Remove client_msg_id column."""
    # Drop the unique index first
    op.drop_index("idx_chat_message_client_msg_id_unique", table_name="chat_message")
    
    # Drop the column
    op.drop_column("chat_message", "client_msg_id")