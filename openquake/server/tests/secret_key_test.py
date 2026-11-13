import pytest
from django.core.exceptions import ImproperlyConfigured

from openquake.server import utils


@pytest.fixture
def server_installation(monkeypatch, tmp_path):
    # a server installation with the secret file written by install.py
    monkeypatch.delenv('DJANGO_SECRET_KEY', raising=False)
    monkeypatch.setattr(utils, 'is_server_installation', lambda: True)
    secret_file = tmp_path / 'django_secret.env'
    monkeypatch.setattr(utils, 'DJANGO_SECRET_FILE', str(secret_file))
    return secret_file


def test_secret_key_from_environment(server_installation, monkeypatch):
    monkeypatch.setenv('DJANGO_SECRET_KEY', 'from-env')
    assert utils.get_or_create_django_secret_key() == 'from-env'


def test_secret_key_from_file(server_installation):
    # the key may contain '=' and is quoted, as written by install.py
    server_installation.write_text("DJANGO_SECRET_KEY='ab=c#d$'\n")
    assert utils.get_or_create_django_secret_key() == 'ab=c#d$'


def test_secret_key_missing(server_installation):
    with pytest.raises(ImproperlyConfigured):
        utils.get_or_create_django_secret_key()
