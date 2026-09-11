import pytest

from openquake.baselib import config
import uuid
from openquake.commonlib import logs
from openquake.commonlib.auth import API_KEY
from openquake.server.tests.views_test import start_uvicorn, stop_uvicorn


@pytest.fixture(scope='module')
def api_client():
    server, thread, client = start_uvicorn()
    try:
        yield client
    finally:
        stop_uvicorn(server, thread)


def test_database_api_requires_api_key(api_client):
    response = api_client.session.post(
        api_client.base_url + '/v0/db/engine_version',
        json={'args': []})
    assert response.status_code == 403


def test_database_api_executes_registered_action(api_client):
    response = api_client.session.post(
        api_client.base_url + '/v0/db/engine_version',
        headers={'X-API-Key': API_KEY}, json={'args': []})
    assert response.status_code == 200
    assert response.json().startswith('3.')


def test_database_api_rejects_unknown_action(api_client):
    response = api_client.session.post(
        api_client.base_url + '/v0/db/not_an_action',
        headers={'X-API-Key': API_KEY}, json={'args': []})
    assert response.status_code == 404


def test_dbcmd_can_use_database_api(api_client, monkeypatch):
    monkeypatch.setattr(logs, 'use_server', lambda: True)
    old_server = config.webapi.server
    config.webapi.server = api_client.base_url
    try:
        result = logs.dbcmd('engine_version')
    finally:
        config.webapi.server = old_server
    assert result.startswith('3.')


def test_dbcmd_uses_explicit_write_transaction(api_client, monkeypatch):
    monkeypatch.setattr(logs, 'use_server', lambda: True)
    old_server = config.webapi.server
    config.webapi.server = api_client.base_url
    tag_name = uuid.uuid4().hex[:16]
    try:
        created = logs.dbcmd('create_tag', tag_name)
        deleted = logs.dbcmd('delete_tag', tag_name)
    finally:
        config.webapi.server = old_server
    assert 'success' in created
    assert 'success' in deleted
