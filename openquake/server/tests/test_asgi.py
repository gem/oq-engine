# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from pathlib import Path
import time

import pytest
from django.conf import settings
from django.contrib.staticfiles.finders import get_finders

from openquake.commonlib.auth import API_KEY
from openquake.commonlib.logs import dbcmd

from .views_test import EngineServerTestCase, start_uvicorn, stop_uvicorn


@pytest.fixture
def uvicorn_client():
    """Run the combined ASGI application for the duration of a test."""
    server, thread, client = start_uvicorn()
    try:
        yield client
    finally:
        stop_uvicorn(server, thread)


@pytest.fixture
def classical_result(uvicorn_client):
    """Run a classical calculation and return its hazard map output."""
    datadir = EngineServerTestCase.datadir
    dbcmd('reset_is_running')  # cleanup stuck calculations
    with open(f'{datadir}/classical.zip', 'rb') as archive:
        response = uvicorn_client.post('/v1/calc/run', dict(archive=archive))
    job_id = response.json()['job_id']
    try:
        for _ in range(300):  # 300 seconds of timeout
            if not uvicorn_client.get(
                    '/v1/calc/list', dict(is_running='true')).json():
                break
            time.sleep(1)
        results = uvicorn_client.get(f'/v1/calc/{job_id}/results').json()
        yield next(res for res in results if res['type'] == 'hmaps')
    finally:
        uvicorn_client.post(f'/v1/calc/{job_id}/remove')


def static_paths():
    """Return the files contributed by all installed Django apps."""
    locations = set()
    paths = []
    for finder in get_finders():
        for storage in finder.storages.values():
            location = Path(storage.location)
            if location in locations:
                continue
            locations.add(location)
            paths.extend(
                path.relative_to(location).as_posix()
                for path in location.rglob('*') if path.is_file())
    return sorted(paths)


def test_static_files_are_served(uvicorn_client):
    """Serve static files contributed by every installed Django app."""
    paths = static_paths()
    assert paths

    for path in paths:
        response = uvicorn_client.get(
            settings.STATIC_URL + path)
        assert response.status_code == 200, path
        if path.endswith('.css'):
            assert response.headers['content-type'].startswith('text/css')


def test_calc_count_requires_internal_api_key(uvicorn_client):
    """Keep the internal calculation-count route protected."""
    response = uvicorn_client.get('/v1/calc_list/count')
    assert response.status_code == 403


def test_calc_result_requires_internal_api_key(uvicorn_client):
    """Keep the internal result-export route protected."""
    response = uvicorn_client.get('/v0/calc/result/1')
    assert response.status_code == 403


def test_calc_result_missing(uvicorn_client):
    """Return a 404 for a non-existing result."""
    response = uvicorn_client.get(
        '/v0/calc/result/0', headers={'X-API-Key': API_KEY})
    assert response.status_code == 404


def test_calc_result_downloads_the_file(uvicorn_client, classical_result):
    """Export a result through the FastAPI route and through the Django one."""
    path = '/v0/calc/result/%d' % classical_result['id']
    headers = {'X-API-Key': API_KEY}
    response = uvicorn_client.get(path, dict(export_type='csv'),
                                  headers=headers)
    assert response.status_code == 200
    assert response.content
    assert response.headers['content-disposition'].startswith(
        'attachment; filename=output-%d-' % classical_result['id'])
    # the same file must be downloadable from the public Django endpoint
    response = uvicorn_client.get(
        '/v1/calc/result/%d' % classical_result['id'],
        dict(export_type='csv'))
    assert response.status_code == 200
    assert response.content == (  # streamed by the Django proxy
        uvicorn_client.get(path, dict(export_type='csv'),
                           headers=headers).content)
    # a failing export is a 500, propagated by the Django proxy as well
    assert uvicorn_client.get(
        path, dict(export_type='gibberish'), headers=headers
    ).status_code == 500
    assert uvicorn_client.get(
        '/v1/calc/result/%d' % classical_result['id'],
        dict(export_type='gibberish')).status_code == 500
