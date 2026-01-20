# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# oq-geoviewer
# Copyright (C) 2018-2019 GEM Foundation
#
# oq-geoviewer is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# oq-geoviewer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# import subprocess
from django.apps import apps as django_apps
from django.core.management import call_command, get_commands
import sys
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = ("Command that run a '<app_name>_postinstall' command if it exists")

    def add_arguments(self, parser):
        parser.add_argument('django_app',
                            help='django application name')

    def handle(self, *args, **options):
        found = False
        for app in django_apps.get_app_configs():
            label = app.label
            if options['django_app'] == label:
                found = True
                break

        if not found:
            self.stdout.write(
                self.style.ERROR(
                    "No django app '%s' found." % (options['django_app'],))
                )
            sys.exit(1)

        postinstall_cmd = options['django_app'] + '_postinstall'
        django_cmds = get_commands()
        if not (postinstall_cmd in django_cmds):
            self.stdout.write(
                self.style.WARNING(
                    "No 'postinst' action needed for app %s, skipped." % (options['django_app'],))
                )
            sys.exit(0)

        call_command(postinstall_cmd)
