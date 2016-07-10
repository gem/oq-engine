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


class FakeJob(object):
    def __init__(self, job_type, calculation_mode):
        self.job_type = job_type
        self.calculation_mode = calculation_mode

    def get_oqparam(self):
        m = mock.Mock()
        m.calculation_mode = self.calculation_mode
        return m


class CheckHazardRiskConsistencyTestCase(unittest.TestCase):
    def test_ok(self):
        haz_job = FakeJob('hazard', 'scenario')
        actions.check_hazard_risk_consistency(
            haz_job, 'scenario_risk')

    def test_obsolete_mode(self):
        haz_job = FakeJob('hazard', 'scenario')
        with self.assertRaises(ValueError) as ctx:
            actions.check_hazard_risk_consistency(
                haz_job, 'scenario')
        msg = str(ctx.exception)
        self.assertEqual(msg, 'Please change calculation_mode=scenario into '
                         'scenario_risk in the .ini file')

    def test_inconsistent_mode(self):
        haz_job = FakeJob('hazard', 'scenario')
        with self.assertRaises(actions.InvalidCalculationID) as ctx:
            actions.check_hazard_risk_consistency(
                haz_job, 'classical_risk')
        msg = str(ctx.exception)
        self.assertEqual(
            msg, "In order to run a risk calculation of kind "
            "'classical_risk', you need to provide a "
            "calculation of kind ['classical', 'classical_risk'], "
            "but you provided a 'scenario' instead")
