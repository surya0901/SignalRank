"""Movie catalog and versioned public ratings; application users are separate."""

import sqlalchemy as sa

from alembic import op

revision = "0001_catalog"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "movies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("title", sa.String(500), nullable=False),
    )
    op.create_table("genres", sa.Column("name", sa.String(50), primary_key=True))
    op.create_table(
        "movie_genres",
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id"), primary_key=True),
        sa.Column("genre", sa.String(50), sa.ForeignKey("genres.name"), primary_key=True),
    )
    op.create_table(
        "dataset_ratings",
        sa.Column("user_id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id"), primary_key=True),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("rated_at", sa.Integer(), nullable=False),
        sa.CheckConstraint("rating >= 0.5 AND rating <= 5 AND rating * 2 = floor(rating * 2)"),
    )
    op.create_index("ix_dataset_ratings_movie_id", "dataset_ratings", ["movie_id"])
    op.create_table(
        "dataset_imports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(1000), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("movie_count", sa.Integer(), nullable=False),
        sa.Column("rating_count", sa.Integer(), nullable=False),
        sa.Column("user_count", sa.Integer(), nullable=False),
        sa.Column(
            "imported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade():
    for table in ["dataset_imports", "dataset_ratings", "movie_genres", "genres", "movies"]:
        op.drop_table(table)
