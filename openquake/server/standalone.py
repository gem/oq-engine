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
"""
import subprocess

WHEELHOUSE_URL = "https://wheelhouse.openquake.org/unified/"
URL_STANDALONE = "https://wheelhouse.openquake.org/py/standalone/post-inst/"
STANDALONE_APP_INFO = [
    # All engine Django app need oq-platform-standalone
    {"pkg": "oq-platform-standalone", "name": None, "ver": "~=2.16.4"},
    # Django apps to install
    {"pkg": "oq-platform-ipt", "name": "openquakeplatform_ipt", "ver": "~=1.21.0"},
    {"pkg": "oq-platform-taxonomy", "name": "openquakeplatform_taxonomy",
     "ver": "~=1.2.0"},
    {"pkg": "django-gem-taxonomy", "name": "django_gem_taxonomy", "ver": "~=1.4.4"},
]


def install_standalone(pycmd, apps=STANDALONE_APP_INFO):
    """
    Install the standalone Django applications if possible.

    :param pycmd: the Python executable to run pip with
    :param apps: the standalone applications to install
    :returns: the errors of the installation, empty if all went well
    """
    errors = []
    for app in apps:
        try:
            print(f"Applications {app['pkg']} are not installed yet \n")
            subprocess.check_call(
                [pycmd, "-m", "pip", "install",
                 "--no-index", "--no-cache-dir",
                 "--find-links", WHEELHOUSE_URL,
                 "--find-links", URL_STANDALONE,
                 app["pkg"] + app["ver"]])
        except Exception as exc:
            # for instance if somebody removed a wheel from the wheelhouse
            errors.append(f"{exc}: could not install {app['pkg']}")
    return errors


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
