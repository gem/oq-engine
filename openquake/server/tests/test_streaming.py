# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio
from io import BytesIO
from types import SimpleNamespace

from django.core.handlers.asgi import ASGIRequest

from openquake.server import views


class UpstreamResponse:
    """Fake upstream that records reads and cleanup for proxy tests."""

    def __init__(self):
        self.status_code = 200
        self.headers = {'Content-Type': 'application/octet-stream'}
        self.chunk_sizes = []
        self.chunks_read = 0
        self.close_calls = 0

    def iter_content(self, chunk_size):
        self.chunk_sizes.append(chunk_size)
        for chunk in (b'first chunk', b'second chunk'):
            self.chunks_read += 1
            yield chunk

    def close(self):
        self.close_calls += 1


def _request(asgi):
    # Use Django's real ASGI request type to exercise request detection.
    if asgi:
        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/v0/test-file',
            'query_string': b'',
            'headers': [(b'host', b'testserver')],
            'server': ('testserver', 80),
            'scheme': 'http',
        }
        return ASGIRequest(scope, BytesIO())
    return SimpleNamespace(
        method='GET', META={'HTTP_HOST': 'testserver'},
        is_secure=lambda: False)


def _proxy_response(monkeypatch, asgi):
    # Stub requests so the test needs neither the API server nor a database.
    upstream = UpstreamResponse()
    monkeypatch.setattr(
        views.requests, 'request', lambda *args, **kwargs: upstream)
    response = views._call_api_file(_request(asgi), 'v0/test-file')
    return response, upstream


async def _consume_asgi(response, upstream):
    # Exercise the async iteration entry point Django uses under ASGI.
    iterator = response.__aiter__()
    chunks = [await iterator.__anext__()]
    # A synchronous fallback would already have read both chunks here.
    chunks_read_after_first = upstream.chunks_read
    chunks.extend([chunk async for chunk in iterator])
    return chunks, chunks_read_after_first


def test_call_api_file_streams_asgi_response_incrementally(monkeypatch):
    response, upstream = _proxy_response(monkeypatch, asgi=True)

    chunks, chunks_read_after_first = asyncio.run(
        _consume_asgi(response, upstream))

    assert chunks_read_after_first == 1
    assert response.is_async
    assert chunks == [b'first chunk', b'second chunk']
    assert upstream.chunk_sizes == [views._CHUNK_SIZE]
    assert upstream.close_calls == 1
    # Django closes the response after sending; EOF already closed upstream.
    response.close()
    assert upstream.close_calls == 1


def test_call_api_file_keeps_wsgi_response_synchronous(monkeypatch):
    # WSGI should continue to use the existing synchronous iterator.
    response, upstream = _proxy_response(monkeypatch, asgi=False)

    assert not response.is_async
    assert list(response.streaming_content) == [
        b'first chunk', b'second chunk']
    assert upstream.chunk_sizes == [views._CHUNK_SIZE]
    assert upstream.close_calls == 1
