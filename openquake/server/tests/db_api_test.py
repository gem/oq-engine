import tempfile
import pytest

from openquake.baselib import config
import uuid
from openquake.commonlib import logs, dbapi
from openquake.commonlib.auth import API_KEY
from openquake.server.tests.views_test import start_webui, stop_webui


@pytest.fixture(scope='module')
def api_client():
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


# the column names passed with ?S, ?D, ?A and ?O are inserted in the SQL
# text, so anything that is not a plain name must be rejected
SUBQUERY = "description=(SELECT max(id) FROM job), status"


def test_match_accepts_plain_column_names():
    assert dbapi.match('UPDATE job SET ?D WHERE id=?x',
                       {'status': 'complete', 'is_running': 0}, 1) == (
        'UPDATE job SET is_running=?, status=? WHERE id=?',
        (0, 'complete', 1))
    assert dbapi.match('SELECT * FROM job AS j WHERE ?A',
                       {'j.is_running': 1, 'j.user_name': None}) == (
        'SELECT * FROM job AS j WHERE j.is_running=? AND '
        'j.user_name IS NULL', (1,))
    assert dbapi.match('INSERT INTO job (?S) VALUES (?X)',
                       ['id', 'status'], [1, 'created']) == (
        'INSERT INTO job (id, status) VALUES (?, ?)', (1, 'created'))


def test_match_rejects_unsafe_column_names():
    for name in [SUBQUERY, 'id; DROP TABLE job', 'status--', '1=1 OR id',
                 'a.b.c', 'id)', '{0}', '']:
        for templ in ['UPDATE job SET ?D WHERE id=?x',
                      'SELECT * FROM job WHERE ?A',
                      'SELECT * FROM job WHERE ?O']:
            args = ({name: 'x'}, 1) if '?x' in templ else ({name: 'x'},)
            with pytest.raises(dbapi.InvalidName):
                dbapi.match(templ, *args)
        with pytest.raises(dbapi.InvalidName):
            dbapi.match('INSERT INTO job (?S) VALUES (?X)', [name], ['x'])


def test_database_api_rejects_unsafe_column_names(api_client):
    # a column name containing a subquery must not reach the database
    headers = {'X-API-Key': API_KEY}

    def call(action, *args):
        return api_client.session.post(
            f'{api_client.base_url}/v0/db/{action}',
            json={'args': list(args)}, headers=headers)

    def get_description():
        job = dbapi.from_json(call('get_job', job_id).json())
        return job.description

    job_id = call('create_job', tempfile.gettempdir()).json()
    try:
        ret = call('update_job', job_id, {SUBQUERY: 'x'})
        assert ret.status_code == 400, ret.text
        assert get_description() == 'just created'
        # plain column names still work
        ret = call('update_job', job_id, {'description': 'updated'})
        assert ret.status_code == 200, ret.text
        assert get_description() == 'updated'
    finally:
        call('update_job', job_id, {'status': 'deleted'})
