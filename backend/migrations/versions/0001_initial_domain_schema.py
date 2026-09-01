"""initial domain schema

Revision ID: 0001
Revises:
Create Date: 2026-08-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    order_status = postgresql.ENUM(
        "CREATED", "PAID", "UNPAID", "CANCELLED",
	name="order_status",
	create_type=False,
    )
    payment_status = postgresql.ENUM(
        "INITIATED", "AUTHORIZED", "CAPTURED", "FAILED", "REFUNDED",
        name="payment_status",
	create_type=False,
    )
    scenario_type = postgresql.ENUM(
        "ABANDONED_CHECKOUT", "AMBIGUOUS_PAYMENT", "ORDER_PAYMENT_MISMATCH",
        name="scenario_type",
	create_type=False,
    )
    workflow_state = postgresql.ENUM(
        "DETECTED", "INVESTIGATING", "RECONSTRUCTED", "DECISION_READY",
        "AWAITING_PERMISSION", "ACTION_PENDING", "ACTION_EXECUTING",
        "VERIFYING", "RECOVERED", "RESOLVED", "ESCALATED", "BLOCKED",
        name="workflow_state",
	create_type=False,
    )
    money_state = postgresql.ENUM(
        "SAFE", "AT_RISK", "RECOVERABLE", "UNKNOWN", "RESOLVED",
        name="money_state",
	create_type=False,
    )
    reconstruction_status = postgresql.ENUM(
        "PENDING", "IN_PROGRESS", "COMPLETE", "PARTIAL", "CONFLICTED",
        name="reconstruction_status",
	create_type=False,
    )

    for enum_type in [
        order_status, payment_status, scenario_type,
        workflow_state, money_state, reconstruction_status
    ]:
        enum_type.create(op.get_bind(), checkfirst=True)

    uuid = postgresql.UUID(as_uuid=True)
    json_type = postgresql.JSONB()

    op.create_table(
        "merchants",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("metadata", json_type),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "customers",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("merchant_id", uuid, sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("external_ref", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("email", sa.String(320)),
        sa.Column("phone", sa.String(64)),
        sa.Column("metadata", json_type),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("merchant_id", "external_ref", name="uq_customer_merchant_external_ref"),
    )

    op.create_table(
        "orders",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("merchant_id", uuid, sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("customer_id", uuid, sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("external_ref", sa.String(255), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", order_status, nullable=False),
        sa.Column("metadata", json_type),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("merchant_id", "external_ref", name="uq_order_merchant_external_ref"),
        sa.CheckConstraint("amount > 0", name="ck_order_amount_positive"),
    )

    op.create_table(
        "payments",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("merchant_id", uuid, sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("order_id", uuid, sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("customer_id", uuid, sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("method", sa.String(64), nullable=False),
        sa.Column("status", payment_status, nullable=False),
        sa.Column("authorized_at", sa.DateTime(timezone=True)),
        sa.Column("captured_at", sa.DateTime(timezone=True)),
        sa.Column("failed_at", sa.DateTime(timezone=True)),
        sa.Column("refunded_at", sa.DateTime(timezone=True)),
        sa.Column("razorpay_payment_id", sa.String(255)),
        sa.Column("metadata", json_type),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
    )

    op.create_table(
        "events",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("merchant_id", uuid, sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("payment_id", uuid, sa.ForeignKey("payments.id")),
        sa.Column("order_id", uuid, sa.ForeignKey("orders.id")),
        sa.Column("customer_id", uuid, sa.ForeignKey("customers.id")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("payload", json_type, nullable=False),
        sa.Column("sequence_hint", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("merchant_id", "source", "event_id", name="uq_event_merchant_source_event_id"),
    )
    op.create_index("ix_events_merchant_occurred_at", "events", ["merchant_id", "occurred_at"])
    op.create_index("ix_events_payment_occurred_at", "events", ["payment_id", "occurred_at"])
    op.create_index("ix_events_order_occurred_at", "events", ["order_id", "occurred_at"])

    op.create_table(
        "cases",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("case_number", sa.String(32), nullable=False, unique=True),
        sa.Column("merchant_id", uuid, sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("scenario_type", scenario_type, nullable=False),
        sa.Column("customer_id", uuid, sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("order_id", uuid, sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("payment_id", uuid, sa.ForeignKey("payments.id")),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("workflow_state", workflow_state, nullable=False),
        sa.Column("money_state", money_state, nullable=False),
        sa.Column("reconstruction_status", reconstruction_status, nullable=False),
        sa.Column("risk_score", sa.Float()),
        sa.Column("recovery_probability", sa.Float()),
        sa.Column("expected_recovery", sa.Integer()),
        sa.Column("recommended_action", sa.String(64)),
        sa.Column("decision_confidence", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_case_amount_positive"),
        sa.CheckConstraint("(risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 1))", name="ck_case_risk_score"),
        sa.CheckConstraint("(recovery_probability IS NULL OR (recovery_probability >= 0 AND recovery_probability <= 1))", name="ck_case_recovery_probability"),
        sa.CheckConstraint("(decision_confidence IS NULL OR (decision_confidence >= 0 AND decision_confidence <= 1))", name="ck_case_decision_confidence"),
        sa.CheckConstraint("(expected_recovery IS NULL OR expected_recovery >= 0)", name="ck_case_expected_recovery"),
    )


def downgrade() -> None:
    op.drop_table("cases")
    op.drop_index("ix_events_order_occurred_at", table_name="events")
    op.drop_index("ix_events_payment_occurred_at", table_name="events")
    op.drop_index("ix_events_merchant_occurred_at", table_name="events")
    op.drop_table("events")
    op.drop_table("payments")
    op.drop_table("orders")
    op.drop_table("customers")
    op.drop_table("merchants")

    bind = op.get_bind()
    for name in [
        "reconstruction_status", "money_state", "workflow_state",
        "scenario_type", "payment_status", "order_status"
    ]:
        postgresql.ENUM(name=name).drop(bind, checkfirst=True)
