import tempfile
import pytest

from openquake.baselib import config
import uuid
from openquake.commonlib import logs, dbapi
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


def test_set_preferred_job_for_missing_job_keeps_db_writable(
        api_client, tmp_path):
    # setting as preferred a job that does not exist used to leave a
    # transaction open: the following writes on the same connection were
    # never committed and the next BEGIN failed with "cannot start a
    # transaction within a transaction"
    headers = {'X-API-Key': API_KEY}

    def call(action, *args):
        return api_client.session.post(
            f'{api_client.base_url}/v0/db/{action}',
            json={'args': list(args)}, headers=headers).json()

    tag_name = uuid.uuid4().hex[:16]
    ret = call('set_preferred_job_for_tag', 999999999, tag_name)
    assert 'error' in ret, ret
    job_id = call('create_job', str(tmp_path))
    try:
        ret = call('set_preferred_job_for_tag', job_id, tag_name)
        assert 'success' in ret, ret
        ret = call('get_preferred_job_for_tag', tag_name)
        assert ret.get('job_id') == job_id, ret
    finally:
        call('delete_tag', tag_name)
        call('update_job', job_id, {'status': 'deleted'})


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
