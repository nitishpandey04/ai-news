"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("phone_number", sa.String(20), nullable=False, unique=True),
        sa.Column("display_name", sa.String(100)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("delivery_time", sa.Time, nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("topics", postgresql.ARRAY(sa.String), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "uq_user_active_sub",
        "subscriptions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_table(
        "news_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("fetch_date", sa.Date, nullable=False, unique=True),
        sa.Column("snippets", postgresql.JSONB, nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("source", sa.String(50), nullable=False, server_default="mock_api"),
    )

    op.create_table(
        "delivery_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscriptions.id")),
        sa.Column("news_cache_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("news_cache.id")),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("whatsapp_message_id", sa.String(100)),
        sa.Column("error_detail", sa.Text),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_delivery_logs_user_id", "delivery_logs", ["user_id"])
    op.create_index("idx_delivery_logs_status", "delivery_logs", ["status"])
    op.create_index("idx_delivery_logs_scheduled_for", "delivery_logs", ["scheduled_for"])


def downgrade() -> None:
    op.drop_table("delivery_logs")
    op.drop_table("news_cache")
    op.drop_index("uq_user_active_sub", table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_table("users")
