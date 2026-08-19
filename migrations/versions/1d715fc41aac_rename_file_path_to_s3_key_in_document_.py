"""rename file_path to s3_key in document_versions

Revision ID: 1d715fc41aac
Revises: 2ea81d2f2ec2
Create Date: 2026-08-17 13:59:06.565030

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1d715fc41aac"
down_revision: str | Sequence[str] | None = "2ea81d2f2ec2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("document_versions", "file_path", new_column_name="s3_key")


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("document_versions", "s3_key", new_column_name="file_path")
