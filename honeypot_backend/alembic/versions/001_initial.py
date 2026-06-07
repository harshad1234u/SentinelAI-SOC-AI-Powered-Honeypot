"""Initial migration — create all five core tables.

Revision ID: 001
Revises: None
Create Date: 2026-06-01

Creates:
- attacks
- ai_analyses
- alerts
- country_stats
- honeypot_sessions
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── attacks ──────────────────────────────────────────────────────────
    op.create_table(
        "attacks",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="Primary key (UUID v4)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Row creation timestamp (UTC)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
            comment="Last update timestamp (UTC)",
        ),
        # Timestamp & source
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="When the attack was observed",
        ),
        sa.Column(
            "src_ip",
            sa.String(45),
            nullable=False,
            comment="Source IP address (v4 or v6)",
        ),
        # Geolocation
        sa.Column("src_country", sa.String(100), comment="Resolved source country name"),
        sa.Column("src_country_code", sa.String(3), comment="ISO 3166-1 alpha-2 country code"),
        sa.Column("src_city", sa.String(100), comment="Resolved source city"),
        sa.Column("src_lat", sa.Float(), comment="Source latitude"),
        sa.Column("src_lon", sa.Float(), comment="Source longitude"),
        sa.Column("src_asn", sa.String(200), comment="Autonomous System Name / Number"),
        # Connection
        sa.Column("dst_port", sa.Integer(), comment="Destination port targeted"),
        sa.Column("service", sa.String(50), comment="Service name (ssh, telnet, http, …)"),
        sa.Column("username", sa.String(255), comment="Attempted username"),
        sa.Column("password", sa.String(255), comment="Attempted password"),
        sa.Column("command", sa.Text(), comment="Command executed in the honeypot shell"),
        # Classification
        sa.Column("severity", sa.String(20), comment="Severity level: low / medium / high / critical"),
        sa.Column("attack_type", sa.String(100), comment="Attack classification"),
        sa.Column("honeypot_type", sa.String(20), comment="Honeypot source: cowrie / opencanary"),
        sa.Column("session_id", sa.String(100), comment="Honeypot session identifier"),
        # Raw data
        sa.Column("raw_log", postgresql.JSONB(astext_type=sa.Text()), comment="Original un-parsed log entry"),
        sa.Column(
            "vector_indexed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
            comment="Whether this row has been embedded into Qdrant",
        ),
        # Threat intelligence
        sa.Column("abuse_confidence", sa.Integer(), comment="AbuseIPDB confidence score 0-100"),
        sa.Column("isp", sa.String(200), comment="ISP reported by AbuseIPDB"),
        sa.Column("usage_type", sa.String(100), comment="IP usage type (Data Center, ISP, …)"),
        sa.Column("total_reports", sa.Integer(), comment="Total abuse reports in AbuseIPDB"),
        sa.Column("reputation", sa.String(20), comment="Reputation label: clean / suspicious / malicious"),
        # Unified threat score
        sa.Column("threat_score", sa.Integer(), comment="Unified 0-100 composite threat score"),
        # PK
        sa.PrimaryKeyConstraint("id"),
    )

    # Single-column indexes for attacks
    op.create_index("ix_attacks_timestamp", "attacks", ["timestamp"])
    op.create_index("ix_attacks_src_ip", "attacks", ["src_ip"])
    op.create_index("ix_attacks_src_country", "attacks", ["src_country"])
    op.create_index("ix_attacks_service", "attacks", ["service"])
    op.create_index("ix_attacks_severity", "attacks", ["severity"])
    op.create_index("ix_attacks_honeypot_type", "attacks", ["honeypot_type"])
    op.create_index("ix_attacks_reputation", "attacks", ["reputation"])
    op.create_index("ix_attacks_threat_score", "attacks", ["threat_score"])

    # Composite indexes for attacks
    op.create_index("ix_attacks_timestamp_severity", "attacks", ["timestamp", "severity"])
    op.create_index("ix_attacks_timestamp_threat_score", "attacks", ["timestamp", "threat_score"])

    # ── ai_analyses ──────────────────────────────────────────────────────
    op.create_table(
        "ai_analyses",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="Primary key (UUID v4)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Row creation timestamp (UTC)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
            comment="Last update timestamp (UTC)",
        ),
        sa.Column("attack_id", sa.Uuid(), nullable=False, comment="FK to the analysed attack"),
        sa.Column("summary", sa.Text(), comment="Human-readable summary of the attack"),
        sa.Column("severity", sa.String(20), comment="AI-assessed severity"),
        sa.Column("attack_type", sa.String(100), comment="AI-classified attack type"),
        sa.Column("recommendation", sa.Text(), comment="Recommended remediation steps"),
        sa.Column(
            "attack_chain",
            postgresql.JSONB(astext_type=sa.Text()),
            comment="Structured MITRE ATT&CK chain mapping",
        ),
        sa.Column("threat_actor_profile", sa.Text(), comment="Inferred threat actor description"),
        sa.Column("confidence", sa.Float(), comment="Model confidence score 0.0-1.0"),
        sa.Column("model_used", sa.String(100), comment="Name of the LLM model used"),
        sa.Column("prompt_version", sa.String(20), comment="Prompt template version identifier"),
        sa.Column("tokens_used", sa.Integer(), comment="Total tokens consumed"),
        sa.Column("analysis_type", sa.String(20), comment="Analysis mode: realtime or investigation"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["attack_id"],
            ["attacks.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_ai_analyses_attack_id", "ai_analyses", ["attack_id"])

    # ── alerts ───────────────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="Primary key (UUID v4)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Row creation timestamp (UTC)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
            comment="Last update timestamp (UTC)",
        ),
        sa.Column("alert_type", sa.String(50), comment="Notification channel"),
        sa.Column("src_ip", sa.String(45), comment="Source IP that triggered the alert"),
        sa.Column("severity", sa.String(20), comment="Severity that triggered the alert"),
        sa.Column("message", sa.Text(), comment="Alert message body"),
        sa.Column("sent_at", sa.DateTime(timezone=True), comment="When the alert was dispatched"),
        sa.Column("status", sa.String(20), comment="Delivery status: sent / failed / suppressed"),
        sa.Column("cooldown_key", sa.String(100), comment="De-duplication key for cooldown logic"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── country_stats ────────────────────────────────────────────────────
    op.create_table(
        "country_stats",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="Primary key (UUID v4)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Row creation timestamp (UTC)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
            comment="Last update timestamp (UTC)",
        ),
        sa.Column(
            "country_code",
            sa.String(3),
            nullable=False,
            comment="ISO 3166-1 alpha-2 country code",
        ),
        sa.Column("country_name", sa.String(100), comment="Full country name"),
        sa.Column(
            "attack_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
            comment="Total attacks from this country",
        ),
        sa.Column("last_seen", sa.DateTime(timezone=True), comment="Most recent attack timestamp"),
        sa.Column("lat", sa.Float(), comment="Country centroid latitude"),
        sa.Column("lon", sa.Float(), comment="Country centroid longitude"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("country_code", name="uq_country_stats_country_code"),
    )

    # ── honeypot_sessions ────────────────────────────────────────────────
    op.create_table(
        "honeypot_sessions",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="Primary key (UUID v4)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Row creation timestamp (UTC)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
            comment="Last update timestamp (UTC)",
        ),
        sa.Column(
            "session_id",
            sa.String(100),
            nullable=False,
            comment="Honeypot-assigned session identifier",
        ),
        sa.Column("src_ip", sa.String(45), comment="Source IP of the attacker"),
        sa.Column("start_time", sa.DateTime(timezone=True), comment="Session start timestamp"),
        sa.Column("end_time", sa.DateTime(timezone=True), comment="Session end timestamp"),
        sa.Column(
            "commands_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
            comment="Number of commands executed",
        ),
        sa.Column("honeypot_type", sa.String(20), comment="Honeypot source: cowrie / opencanary"),
        sa.Column(
            "commands_log",
            postgresql.JSONB(astext_type=sa.Text()),
            comment="Ordered list of command entries",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", name="uq_honeypot_sessions_session_id"),
    )
    op.create_index("ix_honeypot_sessions_session_id", "honeypot_sessions", ["session_id"])


def downgrade() -> None:
    op.drop_table("honeypot_sessions")
    op.drop_table("country_stats")
    op.drop_table("alerts")
    op.drop_table("ai_analyses")
    op.drop_table("attacks")
