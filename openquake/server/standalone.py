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

# Keep this list in sync with the standalone installer install.py.
# NOTE: install.py is outside openquake and can not be imported here
STANDALONE_APP_INFO = [
    # All engine Django app need oq-platform-standalone
    # {"pkg": "oq-platform-standalone", "name": None, "ver": "~=2.16.4"},
    {"pkg": "https://github.com/gem/oq-platform-standalone/archive/refs/heads/django52.zip",
     "name": None, "ver": ""},
    # Django apps to install
    # {"pkg": "oq-platform-ipt", "name": "openquakeplatform_ipt",
    #  "ver": "~=1.21.0"},
    {"pkg": "https://github.com/gem/oq-platform-ipt/archive/refs/heads/django52.zip",
     "name": "openquakeplatform_ipt", "ver": ""},
    # {"pkg": "oq-platform-taxonomy", "name": "openquakeplatform_taxonomy",
    #  "ver": "~=1.2.0"},
    {"pkg": "https://github.com/gem/oq-platform-taxonomy/archive/refs/heads/django52.zip",
     "name": "openquakeplatform_taxonomy", "ver": ""},
    # {"pkg": "django-gem-taxonomy", "name": "django_gem_taxonomy",
    #  "ver": "~=1.4.4"},
    {"pkg": "https://github.com/gem/django-gem-taxonomy/archive/refs/heads/django52.zip",
     "name": "django_gem_taxonomy", "ver": ""}]


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
