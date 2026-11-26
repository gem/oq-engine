# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
"""
Standalone OpenQuake Django applications distributed with the engine, and
the postinstall commands run after their installation.

Run as ``python -m openquake.server.postinstall`` (e.g. as ExecStartPre of
the gunicorn systemd unit) it checks that the engine database is updated
and then runs the postinstall commands, exiting with an error otherwise.
"""
import subprocess
import sys

from openquake.commonlib import dbapi
from openquake.server.db import actions
from openquake.server.db.upgrade_manager import VersioningNotInstalled

# Keep this list in sync with the standalone installer install.py.
# NOTE: install.py is outside openquake and can not be imported here
STANDALONE_APP_INFO = [
    # All engine Django app need oq-platform-standalone
    {"pkg": "oq-platform-standalone", "name": None, "ver": "~=2.19.1"},
    # Django apps to install
    {"pkg": "oq-platform-ipt", "name": "openquakeplatform_ipt",
     "ver": "~=1.22.1"},
    {"pkg": "oq-platform-taxonomy", "name": "openquakeplatform_taxonomy",
     "ver": "~=1.2.1"},
    {"pkg": "django-gem-taxonomy", "name": "django_gem_taxonomy",
     "ver": "~=1.5.1"}]


def postinstall(pycmd, apps=STANDALONE_APP_INFO):
    """
    Run the Django ``migrate`` command and the ``<app>_postinstall``
    commands of the standalone Django applications.

    :param pycmd: the Python executable to run the management commands
                  with
    :param apps: the standalone applications to postinstall
    :returns: the errors of the postinstall, empty if all went well
    """
    errors = []
    try:
        subprocess.check_call(
            [pycmd, "-m", "openquake.server.manage", "migrate"])
    except Exception as exc:
        errors.append(f"error during migrate: {exc}")
    for app in apps:
        if not app["name"]:
            continue  # the standalone applications need no postinstall
        try:
            subprocess.check_call(
                [pycmd, "-m", "openquake.server.manage",
                 "openquake_engine_postinstall", app["name"]])
        except Exception as exc:
            errors.append(f"{exc}: error during {app['name']} postinstall "
                          "command execution")
    return errors


if __name__ == '__main__':
    # Check the engine schema before Django migrations or app hooks write.
    try:
        outdated = actions.check_outdated(dbapi.db)
    except VersioningNotInstalled:
        outdated = ('The database has not been created yet. '
                    'Run oq engine --upgrade-db to create it.')
    if outdated:
        sys.exit(
            f'{dbapi.db.path}: {outdated}\nRun the command as the database '
            'owner (openquake in a server installation) before starting '
            'the WebUI.')
    errors = postinstall(sys.executable)
    if errors:
        sys.exit('\n'.join(errors))
