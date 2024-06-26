from datetime import datetime

from application.extensions import DATABASE
from application.common.constants import GameStates
from application.common.pagination import PaginatedApi
from application.models.actions import Actions


class Games(PaginatedApi, DATABASE.Model):
    __tablename__ = "games"
    game_id = DATABASE.Column(DATABASE.Integer, primary_key=True)
    game_steam_id = DATABASE.Column(DATABASE.Integer, unique=True, nullable=False)
    game_steam_build_id = DATABASE.Column(DATABASE.Integer, nullable=False, default=-1)
    game_steam_build_branch = DATABASE.Column(
        DATABASE.String(256), nullable=False, default="public"
    )
    game_install_dir = DATABASE.Column(
        DATABASE.String(256), unique=True, nullable=False
    )
    game_name = DATABASE.Column(DATABASE.String(256), nullable=False)
    game_pretty_name = DATABASE.Column(DATABASE.String(256), nullable=False)

    game_pid = DATABASE.Column(DATABASE.Integer, nullable=True)

    game_created = DATABASE.Column(
        DATABASE.DateTime, default=datetime.utcnow, nullable=False
    )
    game_last_update = DATABASE.Column(
        DATABASE.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    game_state = DATABASE.Column(
        DATABASE.String(25), default=GameStates.NOT_STATE.value, nullable=False
    )

    actions = DATABASE.relationship(
        "Actions",
        foreign_keys="Actions.game_id",
        backref="actions",
        lazy="dynamic",
    )

    def get_all_actions(self):
        return self.actions.all()

    def get_game_actions(self, game_name, action=None):
        game_obj = Games.query.filter_by(game_name=game_name).first()
        if action:
            query = Actions.query.filter_by(game_id=game_obj.game_id)
        else:
            query = Actions.query.filter_by(game_id=game_obj.game_id, type=action)

        return query.all()

    def to_dict(self):
        data = {}

        for column in self.__table__.columns:
            field = column.key

            if getattr(self, field) == []:
                continue

            data[field] = getattr(self, field)

        return data
