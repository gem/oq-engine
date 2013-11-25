# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


import unittest

from openquake.engine.db import routers
from openquake.engine.db import models as oq


class OQRouterTestCase(unittest.TestCase):
    '''
    Tests for the :py:class:`openquake.engine.db.routers.OQRouter` class.
    '''
    def setUp(self):
        self.router = routers.OQRouter()

    def _db_for_read_helper(self, classes, expected_db):
        '''
        Common test logic
        '''
        for cls in classes:
            self.assertEqual(expected_db, self.router.db_for_read(cls()))

    def _db_for_write_helper(self, classes, expected_db):
        '''
        Common test logic
        '''
        for cls in classes:
            self.assertEqual(expected_db, self.router.db_for_write(cls()))

    def test_admin_correct_read_db(self):
        '''
        For each model in the 'admin' schema, test for proper db routing
        for read operations.
        '''
        classes = [oq.RevisionInfo]
        expected_db = 'admin'

        self._db_for_read_helper(classes, expected_db)

    def test_admin_correct_write_db(self):
        '''
        For each model in the 'admin' schema, test for proper db routing
        for write operations.
        '''
        classes = [oq.RevisionInfo]
        expected_db = 'admin'

        self._db_for_write_helper(classes, expected_db)

    def test_hzrdi_read_schema(self):
        '''
        For each model in the 'hzrdi' schema, test for proper db routing
        for read operations.
        '''
        classes = [oq.SiteModel]
        expected_db = 'job_init'

        self._db_for_read_helper(classes, expected_db)

    def test_hzrdi_write_schema(self):
        '''
        For each model in the 'hzrdi' schema, test for proper db routing
        for write operations.
        '''
        classes = [oq.SiteModel]
        expected_db = 'job_init'

        self._db_for_write_helper(classes, expected_db)

    def test_uiapi_read_schema(self):
        '''
        For each model in the 'uiapi' schema, test for proper db routing
        for read operations.
        '''
        classes = [oq.OqJob, oq.Output]
        expected_db = 'job_init'

        self._db_for_read_helper(classes, expected_db)

    def test_uiapi_write_schema(self):
        '''
        For each model in the 'uiapi' schema, test for proper db routing
        for write operations.
        '''
        classes = [oq.OqJob]
        expected_db = 'job_init'

        self._db_for_write_helper(classes, expected_db)
        self._db_for_write_helper([oq.Output], 'job_init')

    def test_hzrdr_read_schema(self):
        '''
        For each model in the 'hzrdr' schema, test for proper db routing
        for read operations.
        '''
        classes = [oq.HazardMap, oq.HazardCurve, oq.HazardCurveData,
                   oq.GmfData]
        expected_db = 'job_init'

        self._db_for_read_helper(classes, expected_db)

    def test_hzrdr_write_schema(self):
        '''
        For each model in the 'hzrdr' schema, test for proper db routing
        for write operations.
        '''
        classes = [oq.HazardMap, oq.HazardCurve, oq.HazardCurveData,
                   oq.GmfData]

        expected_db = 'job_init'

        self._db_for_write_helper(classes, expected_db)

    def test_riskr_read_schema(self):
        '''
        For each model in the 'riskr' schema, test for proper db routing
        for read operations.
        '''
        classes = [oq.LossMap, oq.LossMapData, oq.LossCurve, oq.LossCurveData,
                   oq.AggregateLossCurveData, oq.BCRDistribution,
                   oq.BCRDistributionData]
        expected_db = 'job_init'

        self._db_for_read_helper(classes, expected_db)

    def test_riskr_write_schema(self):
        '''
        For each model in the 'riskr' schema, test for proper db routing
        for write operations.
        '''
        classes = [oq.LossMap, oq.LossMapData, oq.LossCurve, oq.LossCurveData,
                   oq.AggregateLossCurveData, oq.BCRDistribution,
                   oq.BCRDistributionData]
        expected_db = 'job_init'

        self._db_for_write_helper(classes, expected_db)

    def test_riski_correct_read_db(self):
        '''
        For each model in the 'riski' schema, test for proper db routing
        for read operations.
        '''
        classes = [oq.ExposureModel, oq.ExposureData, oq.Occupancy]
        expected_db = 'job_init'

        self._db_for_read_helper(classes, expected_db)

    def test_riski_correct_write_db(self):
        '''
        For each model in the 'riski' schema, test for proper db routing
        for write operations.
        '''
        classes = [oq.ExposureModel, oq.ExposureData]
        expected_db = 'job_init'

        self._db_for_write_helper(classes, expected_db)
