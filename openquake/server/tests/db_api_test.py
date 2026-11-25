import pytest

from openquake.baselib import config
import uuid
from openquake.commonlib import logs
from openquake.commonlib.auth import API_KEY
from openquake.server.tests.views_test import start_webui, stop_webui


@pytest.fixture(scope='module')
def api_client():
    # the server accepts only the host name used by the client, so that
    # requests using another name can be refused
    server, thread, client = start_webui({'OQ_ALLOWED_HOSTS': '127.0.0.1'})
    try:
        yield client
    finally:
        stop_webui(server, thread)


def test_database_api_requires_api_key(api_client):
    response = api_client.session.post(
        api_client.base_url + '/v0/db/engine_version')
    assert response.status_code == 403


def test_database_api_executes_registered_action(api_client):
    response = api_client.session.post(
        api_client.base_url + '/v0/db/engine_version',
        headers={'X-API-Key': API_KEY})
    assert response.status_code == 200
    assert response.json().startswith('3.')


def test_database_api_rejects_unknown_action(api_client):
    response = api_client.session.post(
        api_client.base_url + '/v0/db/not_an_action',
        headers={'X-API-Key': API_KEY})
    assert response.status_code == 404


def test_worker_api_rejects_invalid_configuration(api_client):
    # the configuration is used to build the ssh commands starting the
    # workerpools, so it is validated before doing anything
    url = api_client.base_url + '/v0/worker_status'
    headers = {'X-API-Key': API_KEY}
    for zworkers in [{'host_cores': 'worker1 1;id>/tmp/pwned',
                      'ctrl_port': '1909'},
                     {'host_cores': '127.0.0.1 -1', 'ctrl_port': '1909;id'},
                     {'host_cores': '127.0.0.1 -1'}, ['127.0.0.1 -1']]:
        response = api_client.session.post(
            url, json={'args': [zworkers]}, headers=headers)
        assert response.status_code == 400, zworkers


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


def test_dbcmd_explains_unknown_host(api_client, monkeypatch):
    # a request using a host name not in ALLOWED_HOSTS gets an HTML 400
    # page from Django; the error must point to ALLOWED_HOSTS
    monkeypatch.setattr(logs, 'use_server', lambda: True)
    server = api_client.base_url.replace('127.0.0.1', 'localhost')
    monkeypatch.setenv('OQ_WEBAPI_SERVER', server)
    for action, args in [('engine_version', ()), ('workers_status', ())]:
        with pytest.raises(RuntimeError, match='"localhost" is listed in '
                           'its ALLOWED_HOSTS'):
            logs.dbcmd(action, *args)
    # the errors of the internal API itself do not mention it
    monkeypatch.setenv('OQ_WEBAPI_SERVER', api_client.base_url)
    with pytest.raises(RuntimeError) as ctx:
        logs.dbcmd('workers_status', {'host_cores': '127.0.0.1 -1'})
    assert '400' in str(ctx.value)
    assert 'ALLOWED_HOSTS' not in str(ctx.value)
