# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

# NB: run with OQ_APPLICATION_MODE unset; integration uses a scratch database.
import os
import sys
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from openquake.server import standalone
from openquake.server.management.commands import openquake_engine_postinstall


@pytest.mark.parametrize('app', [
    'openquakeplatform_ipt', 'openquakeplatform_taxonomy',
    'django_gem_taxonomy'])
def test_missing_app_is_skipped(app):
    output = StringIO()
    command = openquake_engine_postinstall.Command(stdout=output)
    with patch.object(openquake_engine_postinstall.django_apps,
                      'get_app_configs', return_value=[]), patch.object(
            openquake_engine_postinstall, 'get_commands') as get_commands:
        assert command.handle(django_app=app) is None
    assert app in output.getvalue()
    assert 'skipped' in output.getvalue()
    get_commands.assert_not_called()


@pytest.mark.parametrize('fails', [False, True])
def test_installed_app_postinstall(fails):
    app = 'openquakeplatform_ipt'
    hook = app + '_postinstall'
    command = openquake_engine_postinstall.Command()
    error = RuntimeError('postinstall failed') if fails else None
    with patch.object(openquake_engine_postinstall.django_apps,
                      'get_app_configs', return_value=[
                          SimpleNamespace(label=app)]), patch.object(
            openquake_engine_postinstall, 'get_commands',
            return_value={hook: app}), patch.object(
                openquake_engine_postinstall, 'call_command',
                side_effect=error) as call_command:
        if fails:
            with pytest.raises(RuntimeError, match='postinstall failed'):
                command.handle(django_app=app)
        else:
            command.handle(django_app=app)
    call_command.assert_called_once_with(hook)


def test_postinstall_with_all_optional_apps_missing(tmp_path, monkeypatch,
                                                  capfd):
    missing = tuple(app['name'] for app in standalone.STANDALONE_APP_INFO
                    if app['name'])
    dbfile = tmp_path / 'postinstall.sqlite3'
    cfgfile = tmp_path / 'openquake.cfg'
    cfgfile.write_text(f'[server]\ndbfile = {dbfile}\n')
    settings = tmp_path / 'postinstall_settings.py'
    settings.write_text(
        'from openquake.server.settings import *\n'
        f'INSTALLED_APPS = tuple(app for app in INSTALLED_APPS\n'
        f'    if app.split(".")[0] not in {missing!r}\n'
        '    and app.split(".")[0] != "openquakeplatform")\n'
        'STANDALONE = False\nSTANDALONE_APPS = ()\n')
    monkeypatch.setenv('OQ_CONFIG_FILE', str(cfgfile))
    monkeypatch.setenv('OQ_DATADIR', str(tmp_path))
    monkeypatch.setenv('OQ_APPLICATION_MODE', 'PUBLIC')
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'postinstall_settings')
    monkeypatch.setenv('PYTHONPATH', os.pathsep.join(
        (str(tmp_path), os.environ.get('PYTHONPATH', ''))))

    errors = standalone.postinstall(sys.executable)
    output = capfd.readouterr().out
    assert errors == []
    assert dbfile.is_file()
    for app in missing:
        assert f"Django app '{app}' is not installed, skipped." in output
