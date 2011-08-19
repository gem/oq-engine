# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


import unittest

from openquake.db import routers
from openquake.db.models import *
from openquake.db.dbview_models import *


class OQRouterTestCase(unittest.TestCase):
    '''
    Tests for the :py:class:`openquake.db.routers.OQRouter` class.
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
        classes = [Organization, OqUser, RevisionInfo]
        expected_db = 'admin'

        self._db_for_read_helper(classes, expected_db)

    def test_admin_correct_write_db(self):
        '''
        For each model in the 'admin' schema, test for proper db routing
        for write operations.
        '''
        classes = [Organization, OqUser, RevisionInfo]
        expected_db = 'admin'

        self._db_for_write_helper(classes, expected_db)

    def test_eqcat_correct_read_db(self):
        '''
        For each model in the 'eqcat' schema, test for proper db routing
        for read operations.
        '''
        classes = [Catalog, Magnitude, Surface]
        expected_db = 'eqcat_read'

        self._db_for_read_helper(classes, expected_db)

    def test_eqcat_correct_write_db(self):
        '''
        For each model in the 'eqcat' schema, test for proper db routing
        for write operations.
        '''
        classes = [Catalog, Magnitude, Surface]
        expected_db = 'eqcat_write'

        self._db_for_write_helper(classes, expected_db)

    def test_hzrdi_correct_read_db(self):
        '''
        For each model in the 'hzrdi' schema, test for proper db routing
        for read operations.
        '''
        classes = [Rupture, Source, SimpleFault, MfdEvd, MfdTgr, ComplexFault,
            RDepthDistr, RRateMdl, FocalMechanism]
        expected_db = 'hzrdi_read'

        self._db_for_read_helper(classes, expected_db)

    def test_hzrdi_correct_write_db(self):
        '''
        For each model in the 'hzrdi' schema, test for proper db routing
        for write operations.
        '''
        classes = [Rupture, Source, SimpleFault, MfdEvd, MfdTgr, ComplexFault,
            RDepthDistr, RRateMdl, FocalMechanism]
        expected_db = 'hzrdi_write'

        self._db_for_write_helper(classes, expected_db)

    def test_uiapi_correct_read_db(self):
        '''
        For each model in the 'uiapi' schema, test for proper db routing
        for read operations.
        '''
        classes = [Upload, Input, OqJob, OqParams, Output, ErrorMsg]
        expected_db = 'uiapi_read'

        self._db_for_read_helper(classes, expected_db)

    def test_uiapi_correct_write_db(self):
        '''
        For each model in the 'uiapi' schema, test for proper db routing
        for write operations.
        '''
        classes = [Upload, Input, OqJob, OqParams, Output, ErrorMsg]
        expected_db = 'uiapi_write'

        self._db_for_write_helper(classes, expected_db)

    def test_hzrdr_correct_read_db(self):
        '''
        For each model in the 'hzrdr' schema, test for proper db routing
        for read operations.
        '''
        classes = [HazardMap, HazardMapData, HazardCurve, HazardCurveData,
            GmfData]
        expected_db = 'hzrdr_read'

        self._db_for_read_helper(classes, expected_db)

    def test_hzrdr_correct_write_db(self):
        '''
        For each model in the 'hzrdr' schema, test for proper db routing
        for write operations.
        '''
        classes = [HazardMap, HazardMapData, HazardCurve, HazardCurveData,
            GmfData]

        expected_db = 'hzrdr_write'

        self._db_for_write_helper(classes, expected_db)

    def test_riskr_correct_read_db(self):
        '''
        For each model in the 'riskr' schema, test for proper db routing
        for read operations.
        '''
        classes = [LossMap, LossMapData, LossCurve, LossCurveData,
            AggregateLossCurveData]
        expected_db = 'riskr_read'

        self._db_for_read_helper(classes, expected_db)

    def test_riskr_correct_write_db(self):
        '''
        For each model in the 'riskr' schema, test for proper db routing
        for write operations.
        '''
        classes = [LossMap, LossMapData, LossCurve, LossCurveData,
            AggregateLossCurveData]
        expected_db = 'riskr_write'

        self._db_for_write_helper(classes, expected_db)

    def test_oqmif_correct_read_db(self):
        '''
        For each model in the 'oqmif' schema, test for proper db routing
        for read operations.
        '''
        classes = [ExposureModel, ExposureData]
        expected_db = 'oqmif'

        self._db_for_read_helper(classes, expected_db)

    def test_oqmif_correct_write_db(self):
        '''
        For each model in the 'oqmif' schema, test for proper db routing
        for write operations.
        '''
        classes = [ExposureModel, ExposureData]
        expected_db = 'oqmif'

        self._db_for_write_helper(classes, expected_db)

    def test_riski_correct_read_db(self):
        '''
        For each model in the 'riski' schema, test for proper db routing
        for read operations.
        '''
        classes = [VulnerabilityModel, VulnerabilityFunction]
        expected_db = 'riski_read'

        self._db_for_read_helper(classes, expected_db)

    def test_riski_correct_write_db(self):
        '''
        For each model in the 'riski' schema, test for proper db routing
        for write operations.
        '''
        classes = [VulnerabilityModel, VulnerabilityFunction]
        expected_db = 'riski_write'

        self._db_for_write_helper(classes, expected_db)


