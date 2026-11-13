import os
import uuid
from unittest import mock

import pytest

from openquake.commonlib import logs
from openquake.engine import engine as engine_mod
from openquake.qa_tests_data.classical import case_01
from openquake.commonlib.auth import API_KEY
from openquake.server.tests.views_test import (
    start_dbserver, start_webui, stop_webui, use_dbserver)


@pytest.fixture(scope='module')
def api_client():
    server, thread, client = start_dbserver()
    try:
        yield client
    finally:
        stop_webui(server, thread)


@pytest.fixture(scope='module')
def webui_client():
    server, thread, client = start_webui()
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


def test_dbserver_does_not_serve_v1(api_client):
    assert api_client.get('/v0/ping').status_code == 200
    assert api_client.get('/v1/ping').status_code == 404
    assert api_client.get('/v1/calc/list').status_code == 404


def test_webui_does_not_serve_v0(webui_client):
    assert webui_client.get('/v1/ping').status_code == 200
    assert webui_client.get('/v0/ping').status_code == 404
    response = webui_client.session.post(
        webui_client.base_url + '/v0/db/engine_version',
        headers={'X-API-Key': API_KEY})
    assert response.status_code == 404


def test_dbcmd_can_use_database_api(api_client):
    with use_dbserver(api_client):
        result = logs.dbcmd('engine_version')
    assert result.startswith('3.')


def test_dbcmd_uses_explicit_write_transaction(api_client):
    tag_name = uuid.uuid4().hex[:16]
    with use_dbserver(api_client):
        created = logs.dbcmd('create_tag', tag_name)
        deleted = logs.dbcmd('delete_tag', tag_name)
    assert 'success' in created
    assert 'success' in deleted


def test_dbcmd_without_dbserver(api_client):
    with use_dbserver(api_client):
        logs.config.dbserver['port'] = 1  # nobody is listening there
        with pytest.raises(RuntimeError, match='DbServer is not running'):
            logs.dbcmd('engine_version')


def test_calculation_through_dbserver(api_client):
    # run a calculation as a regular user of a server installation: every
    # database command, including the logs, must go through the DbServer
    ini = os.path.join(os.path.dirname(case_01.__file__), 'job.ini')
    with use_dbserver(api_client, engine_mod), mock.patch.object(
            logs, '_post_dbserver', wraps=logs._post_dbserver) as post:
        [job] = engine_mod.create_jobs([ini], user_name='dbserver-tester')
        engine_mod.run_jobs([job])
        status = logs.dbcmd('get_job', job.calc_id).status
        log_size = logs.dbcmd('get_log_size', job.calc_id)
    assert status == 'complete'
    assert log_size > 0
    paths = [call.args[0] for call in post.call_args_list]
    assert '/v0/db/create_job' in paths
    assert '/v0/db/log' in paths
    assert '/v0/db/finish' in paths
