from datetime import datetime
from pytest import fixture
from application.config.config import DefaultConfig
from application.factory import create_app


@fixture(scope="session")
def fake_app():
    config = DefaultConfig(deploy_type="python")
    config.HISTORY_START_YEAR = datetime.now().year
    config.obtain_environment_variables()

    app = create_app(config=config)

    yield app
