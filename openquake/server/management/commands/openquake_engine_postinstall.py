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
import json
import os
from importlib.metadata import version

from django.apps import apps as django_apps
from django.core.management import call_command, get_commands
import sys
from django.core.management.base import BaseCommand
from openquake.commonlib.logs import get_datadir


def _taxonomy_postinstall_state():
    # Track both packages so added standard records are synced on upgrades.
    signature = ':'.join((version('django-gem-taxonomy'),
                          version('openquake-gem-taxonomy-data')))
    marker = os.path.join(get_datadir(), '.django_gem_taxonomy_version')
    return marker, signature


def _sync_taxonomy():
    # Add missing standard records without resetting customized database rows.
    # These packages are optional and may not be installed in every setup.
    from django_gem_taxonomy.models import Attribute, AtomsGroup, Atom, Param
    from openquake import gem_taxonomy_data

    data_file = os.path.join(os.path.dirname(gem_taxonomy_data.__file__),
                             'data', 'taxonomy4.0_standard.json')
    with open(data_file) as f:
        data = json.load(f)

    attrs = {}
    for item in data['Attribute']:
        attrs[item['name']], _ = Attribute.objects.get_or_create(
            name=item['name'], defaults={
                'prog': item['prog'], 'title': item['title']})

    groups = {}
    for item in data['AtomsGroup']:
        groups[item['name']], _ = AtomsGroup.objects.get_or_create(
            name=item['name'], defaults={
                'prog': item['prog'], 'title': item['title'],
                'attr': attrs[item['group']]})

    atoms = {}
    atoms['_ARG'], _ = Atom.objects.get_or_create(
        name='_ARG', defaults={
            'prog': 0,
            'title': '',
            'desc': ('Virtual atom dependency to prevent arguments-only '
                     'atoms from being visualized as unconstrained atoms'),
            'args': None, 'params': None,
            'type': json.dumps({'name': 'virtual'}),
            'group': None, 'attr': None})
    for item in data['Atom']:
        name = item['name']
        args = json.loads(item['args']) if item['args'] else None
        params = json.loads(item['params']) if item['params'] else None
        atom_type = data['AtomType'].get(name, json.dumps({}))
        atoms[name], _ = Atom.objects.get_or_create(name=name, defaults={
            'prog': item['prog'], 'title': item['title'],
            'desc': item['desc'], 'args': args, 'params': params,
            'type': atom_type, 'group': groups[item['group']],
            'attr': attrs[item['attr']]})

    for name, dependencies in data['AtomsDeps'].items():
        atoms[name].deps.add(*(atoms[dep] for dep in dependencies))
    for name, denied in data['AtomsDeny'].items():
        atoms[name].deny.add(*(atoms[atom] for atom in denied))
    for atom_name, parameters in data['Param'].items():
        for item in parameters:
            Param.objects.get_or_create(
                atom=atoms[atom_name], name=item['name'], defaults={
                    'title': item['title'], 'desc': item['desc'],
                    'prog': item['prog']})


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
        if postinstall_cmd not in django_cmds:
            self.stdout.write(
                self.style.WARNING(
                    "No 'postinst' action needed for app %s, skipped." % (
                        options['django_app'],))
                )
            sys.exit(0)

        marker = None
        if options['django_app'] == 'django_gem_taxonomy':
            attr_model = django_apps.get_model(
                'django_gem_taxonomy', 'Attribute')
            marker, signature = _taxonomy_postinstall_state()
            if os.path.exists(marker):
                with open(marker) as f:
                    same_version = f.read().strip() == signature
                if same_version and attr_model.objects.exists():
                    self.stdout.write(
                        'Taxonomy data already synced, skipping.')
                    return

        if marker:
            _sync_taxonomy()
            os.makedirs(os.path.dirname(marker), exist_ok=True)
            with open(marker + '.tmp', 'w') as f:
                f.write(signature)
            os.replace(marker + '.tmp', marker)
            return

        call_command(postinstall_cmd)
