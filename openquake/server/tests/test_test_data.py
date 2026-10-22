# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import pathlib
import sqlite3
import pytest
from openquake.commonlib import dbapi
from openquake.server.tests import conftest


def test_cleanup_closes_engine_database(tmp_path, monkeypatch):
    # Emulate Windows refusing to unlink a database with an open connection.
    dbfile = tmp_path / 'test.sqlite3'
    cfgfile = tmp_path / 'test.cfg'
    cfgfile.touch()
    datadir = tmp_path / 'data'
    datadir.mkdir()
    db = dbapi.Db(sqlite3.connect, str(dbfile))
    conn = db.conn
    monkeypatch.setattr(dbapi, 'db', db)
    monkeypatch.setattr(conftest, '_server_cfg_path', str(cfgfile))
    monkeypatch.setattr(conftest, '_test_dbfile', str(dbfile))
    monkeypatch.setattr(conftest, '_test_datadir', str(datadir))
    # The fixture restores both environment variables on exit.
    monkeypatch.setenv('OQ_CONFIG_FILE', str(cfgfile))
    monkeypatch.setenv('OQ_DATADIR', str(datadir))
    unlink = pathlib.Path.unlink

    def windows_unlink(path, *args, **kwargs):
        # A real connection must be closed before attempting file removal.
        if path == dbfile:
            try:
                conn.execute('SELECT 1')
            except sqlite3.ProgrammingError:
                pass  # the connection was closed
            else:
                raise PermissionError('The database is still open')
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, 'unlink', windows_unlink)
    fixture = conftest.server_test_data.__wrapped__()
    next(fixture)
    try:
        with pytest.raises(StopIteration):
            next(fixture)
    finally:
        conn.close()
    assert not dbfile.exists()
    assert not cfgfile.exists()
    assert not datadir.exists()
