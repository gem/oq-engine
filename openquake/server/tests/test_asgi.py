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

import pytest
from django.conf import settings
from django.contrib.staticfiles.finders import get_finders

from .views_test import start_uvicorn, stop_uvicorn


@pytest.fixture
def uvicorn_client():
    """Run the combined ASGI application for the duration of a test."""
    server, thread, client = start_uvicorn()
    try:
        yield client
    finally:
        stop_uvicorn(server, thread)


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
