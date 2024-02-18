"""Add updates to the game server table.

Revision ID: database_v3
Revises:
Create Date: 2023-10-08 14:10:31.088339

"""
from alembic import op
import sqlalchemy as sa

from application.common.constants import GameStates

# revision identifiers, used by Alembic.
revision = "database_v3"
down_revision = "database_v2"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("games", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "game_state",
                sa.String(length=25),
                default=GameStates.NOT_STATE.value,
                nullable=False,
            ),
            insert_after="",
            insert_before="",
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("games", schema=None) as batch_op:
        batch_op.drop_column("game_state")
    # ### end Alembic commands ###
