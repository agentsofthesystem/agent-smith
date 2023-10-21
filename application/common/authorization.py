import jwt

from flask.wrappers import Request

from application.common.exceptions import InvalidUsage
from application.common.exceptions import InvalidUsage
from application.source.models.settings import Settings
from application.source.models.tokens import Tokens


def _verify_bearer_token(request: Request) -> int:
    """This is the bearer token gauntlet, the requests only goal is to get through all of the checks."""

    # Use 401 Unauthorized if token is missing entirely, 403 its there but not allowed.
    headers = request.headers

    if "Authorization" not in headers:
        # raise InvalidUsage("Not Authorized - Missing Authorization", status_code=401)
        return 401

    auth = headers["Authorization"]

    if "Bearer" not in auth:
        # raise InvalidUsage("Not Authorized - Invalid Authorization Type", status_code=401)
        return 401

    bearer_token = auth.split("Bearer")[-1].strip()

    # Make sure it's there first...
    token_lookup = Tokens.query.filter_by(
        token_active=True, token_value=bearer_token
    ).first()

    if token_lookup is None:
        # raise InvalidUsage("Not Authorized - Invalid Token", status_code=403)
        return 403

    # Next decode this bad thing...
    secret_obj = Settings.query.filter_by(setting_name="application_secret").first()

    try:
        decoded_token = jwt.decode(
            bearer_token, secret_obj.setting_value, algorithms="HS256"
        )
    except jwt.exceptions.DecodeError:
        # raise InvalidUsage("Not Authorized - Invalid Token", status_code=403)
        return 403

    # Last check... better equal what's in the database.
    decoded_token_name = decoded_token["token_name"]
    if decoded_token_name != token_lookup.token_name:
        # raise InvalidUsage("Not Authorized - Invalid Token", status_code=403)
        return 403

    return 200