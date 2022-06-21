"""initial

Revision ID: d28f489a20e9
Revises:
Create Date: 2022-04-08 17:12:00.817109

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d28f489a20e9"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sport",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "name", sa.String(length=100), unique=True, nullable=False, index=True
        ),
        sa.Column("slug", sa.String(length=150), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, default=True),
        sa.CheckConstraint("char_length(name) >= 1", name="name_min_length"),
        sa.CheckConstraint("char_length(name) <= 100", name="name_max_length"),
        sa.CheckConstraint("char_length(slug) >= 1", name="slug_min_length"),
        sa.CheckConstraint("char_length(slug) <= 150", name="slug_max_length"),
    )

    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "name", sa.String(length=100), nullable=False, index=True
        ),
        sa.Column("slug", sa.String(150), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "type", sa.Enum("preplay", "inplay", name="event_type"), nullable=False
        ),
        sa.Column("sport_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("Pending", "Started", "Ended", "Cancelled", name="event_status"),
            nullable=False,
        ),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_start", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["sport_id"], ["sport.id"], ondelete="SET NULL"),
        sa.CheckConstraint("char_length(name) >= 1", name="name_min_length"),
        sa.CheckConstraint("char_length(name) <= 100", name="name_max_length"),
        sa.CheckConstraint("char_length(slug) >= 1", name="slug_min_length"),
        sa.CheckConstraint("char_length(slug) <= 150", name="slug_max_length"),
    )

    op.create_table(
        "selection",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "name", sa.String(length=100), nullable=False, index=True
        ),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column(
            "price", sa.DECIMAL(precision=10, scale=2, decimal_return_scale=2), nullable=False
        ),
        sa.Column("active", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "outcome",
            sa.Enum("Unsettled", "Void", "Lose", "Win", name="selection_outcome"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"], ondelete="SET NULL"),
        sa.CheckConstraint("char_length(name) >= 1", name="name_min_length"),
        sa.CheckConstraint("char_length(name) <= 100", name="name_max_length"),
    )


def downgrade():
    op.drop_table("selection")
    op.drop_table("event")
    op.drop_table("sport")

    op.execute("DROP TYPE event_type")
    op.execute("DROP TYPE event_status")
    op.execute("DROP TYPE selection_outcome")
