import datetime
import os

import jwt
import pytest

pytest_plugins = ("pytest_jupyter.jupyter_server",)


@pytest.fixture
def jp_server_config(jp_server_config):
    return {
        "ServerApp": {"jpserver_extensions": {"NaaVRE_communicator_jupyterlab": True}}
        }


@pytest.fixture(scope="session", autouse=True)
def set_env():
    os.environ["VRE_API_VERIFY_SSL"] = "true"
    os.environ["NAAVRE_ALLOWED_DOMAINS"] = "*"
    os.environ["OAUTH_ACCESS_TOKEN"] = ""
    os.environ["OAUTH_REFRESH_TOKEN"] = ""


@pytest.fixture
def valid_access_token():
    """ Get a dummy access token that is not expired
    Returns
    -------
    jwt: str
        jwt-encoded dict with an expiration date set in the future
    """
    exp = (datetime.datetime.now() + datetime.timedelta(hours=1)).timestamp()
    return jwt.encode({'exp': int(exp)}, "dummy-secret")
