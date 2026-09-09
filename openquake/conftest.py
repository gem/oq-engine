# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import signal
import subprocess
import sys
import time

import pytest


@pytest.fixture(scope="session", autouse=True)
def dbserver():
    """Start a DbServer for tests that use the database dispatcher."""
    from openquake.server import dbserver as server

    if server.get_status() == 'running':
        yield None
        return

    cmd = [sys.executable, '-m', 'openquake.commands', 'dbserver',
           'start', '--foreground']
    process = subprocess.Popen(cmd, start_new_session=True)
    deadline = time.monotonic() + 30
    while server.get_status() == 'not-running':
        if process.poll() is not None:
            raise RuntimeError('The test DbServer exited during startup')
        if time.monotonic() >= deadline:
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=5)
            raise RuntimeError('The test DbServer did not start')
        time.sleep(.1)

    try:
        yield process
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
