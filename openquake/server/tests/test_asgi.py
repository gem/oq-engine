# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import pytest
from django.contrib.staticfiles import finders

from openquake.server.tests.views_test import start_uvicorn, stop_uvicorn


@pytest.fixture
def uvicorn_client():
    """Run the combined ASGI application for the duration of a test."""
    server, thread, client = start_uvicorn()
    try:
        yield client
    finally:
        stop_uvicorn(server, thread)


def test_static_files_are_served(uvicorn_client):
    """Serve engine and installed-tool static files through Uvicorn."""
    paths = ['css/base.css']
    if finders.find('ipt/css/ipt.css'):
        paths.append('ipt/css/ipt.css')

    for path in paths:
        response = uvicorn_client.get('/static/' + path)
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('text/css')
