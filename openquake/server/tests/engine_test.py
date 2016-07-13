# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2016 GEM Foundation
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

import os
import getpass
import unittest
import tempfile
import mock

from django.db import connection
from openquake.commonlib import readinput, datastore
from openquake.server.db import models, actions, upgrade_manager
from openquake.server.settings import DATABASE

USER = getpass.getuser()


# twin to engine.job_from_file
def job_from_file(cfg_file, username, datadir, hazard_calculation_id=None):
    oq = readinput.get_oqparam(cfg_file)
    job_id = actions.create_job(oq.calculation_mode, oq.description,
                                username, datadir, hazard_calculation_id)
    return job_id, oq


def setup_module():
    global tmpfile
    fh, tmpfile = tempfile.mkstemp()
    os.close(fh)
    DATABASE['NAME'] = tmpfile
    DATABASE['USER'] = USER
    connection.cursor()  # connect to the db
    # sanity check: make sure we are using the right db
    fname = connection.connection.execute(
        'PRAGMA database_list').fetchone()[-1]
    assert fname == tmpfile, (fname, tmpfile)
    upgrade_manager.upgrade_db(connection.connection)


def teardown_module():
    connection.close()


def get_job(cfg, username, hazard_calculation_id=None):
    job_id, oq = job_from_file(cfg, username, datastore.DATADIR,
                               hazard_calculation_id)
    return models.OqJob.objects.get(pk=job_id)


class FakeOutput(object):
    def __init__(self, id, display_name):
        self.id = id
        self.display_name = display_name

    def get_output_type_display(self):
        return self.display_name + str(self.id)


class PrintSummaryTestCase(unittest.TestCase):
    outputs = [FakeOutput(i, 'gmf') for i in range(1, 12)]

    def print_outputs_summary(self, full):
        got = actions.print_outputs_summary(self.outputs, full)
        return '\n'.join(got)

    def test_print_outputs_summary_full(self):
        self.assertEqual(self.print_outputs_summary(full=True), '''\
  id | name
   1 | gmf
   2 | gmf
   3 | gmf
   4 | gmf
   5 | gmf
   6 | gmf
   7 | gmf
   8 | gmf
   9 | gmf
  10 | gmf
  11 | gmf''')

    def test_print_outputs_summary_short(self):
        self.assertEqual(
            self.print_outputs_summary(full=False), '''\
  id | name
   1 | gmf
   2 | gmf
   3 | gmf
   4 | gmf
   5 | gmf
   6 | gmf
   7 | gmf
   8 | gmf
   9 | gmf
  10 | gmf
 ... | 1 additional output(s)
Some outputs where not shown. You can see the full list with the command
`oq engine --list-outputs`''')
