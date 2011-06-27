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


import os
import unittest

from db.alchemy.db_utils import get_uiapi_writer_session
from db.alchemy.models import LossAssetData, LossCurveData
from openquake.output.risk import LossCurveDBWriter
from openquake.shapes import Site, Curve

from db_tests import helpers

# The data below was captured (and subsequently modified for testing purposes)
# by running
#
#   bin/openquake --config_file=smoketests/classical_psha_simple/config.gem
#
# and putting a breakpoint in openquake/output/risk.py:CurveXMLWriter.write()
RISK_LOSS_CURVE_DATA = [
    (Site(-118.077721, 33.852034),
     (Curve([(3.18e-06, 1.0),(8.81e-06, 1.0),(1.44e-05, 1.0),(2.00e-05, 1.0)]),
      {u'assetValue': 5.07, u'assetID': u'a5625', u'listDescription': u'Collection of exposure values for existing building in Los Angeles County, California, US', u'structureCategory': u'RM1L', u'lon': -118.077721, u'assetDescription': u'LA building', u'vulnerabilityFunctionReference': u'HAZUS_RM1L_LC', u'listID': u'LA01', u'assetValueUnit': None, u'lat': 33.852034})),

    (Site(-118.077721, 33.852034),
     (Curve([(7.18e-06, 1.0),(1.91e-05, 1.0),(3.12e-05, 1.0),(4.32e-05, 1.0)]),
     {u'assetValue': 5.63, u'assetID': u'a5629', u'listDescription': u'Collection of exposure values for existing building in Los Angeles County, California, US', u'structureCategory': u'URML', u'lon': -118.077721, u'assetDescription': u'LA building', u'vulnerabilityFunctionReference': u'HAZUS_URML_LC', u'listID': u'LA01', u'assetValueUnit': None, u'lat': 33.852034})),

    (Site(-118.077721, 33.852034),
     (Curve([(5.48e-06, 1.0),(1.45e-05, 1.0),(2.36e-05, 1.0),(3.27e-05, 1.0)]),
     {u'assetValue': 11.26, u'assetID': u'a5630', u'listDescription': u'Collection of exposure values for existing building in Los Angeles County, California, US', u'structureCategory': u'URML', u'lon': -118.077721, u'assetDescription': u'LA building', u'vulnerabilityFunctionReference': u'HAZUS_URML_LS', u'listID': u'LA01', u'assetValueUnit': None, u'lat': 33.852034})),

    (Site(-118.077721, 33.852034),
     (Curve([(9.77e-06, 1.0),(2.64e-05, 1.0),(4.31e-05, 1.0),(5.98e-05, 1.0)]),
     {u'assetValue': 5.5, u'assetID': u'a5636', u'listDescription': u'Collection of exposure values for existing building in Los Angeles County, California, US', u'structureCategory': u'C3L', u'lon': -118.077721, u'assetDescription': u'LA building', u'vulnerabilityFunctionReference': u'HAZUS_C3L_MC', u'listID': u'LA01', u'assetValueUnit': None, u'lat': 33.852034})),
]


class LossCurveDBWriterTestCase(unittest.TestCase, helpers.DbTestMixin):
    """
    Unit tests for the LossCurveDBWriter class, which serializes
    loss curves to the database.
    """
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    def setUp(self):
        self.job = self.setup_classic_job()
        self.session = get_uiapi_writer_session()
        output_path = self.generate_output_path(self.job)
        self.display_name = os.path.basename(output_path)

        self.writer = LossCurveDBWriter(self.session, output_path, self.job.id)

    def test_insert(self):
        """All the records are inserted correctly."""
        output = self.writer.output

        # Call the function under test.
        data = RISK_LOSS_CURVE_DATA
        self.writer.serialize(data)

        # After calling the function under test we see the expected output.
        self.assertEqual(1, len(self.job.output_set))

        # Make sure the inserted output record has the right data.
        [output] = self.job.output_set
        self.assertTrue(output.db_backed)
        self.assertTrue(output.path is None)
        self.assertEqual(self.display_name, output.display_name)
        self.assertEqual("loss_curve", output.output_type)
        self.assertTrue(self.job is output.oq_job)

        # After calling the function under test we see the expected loss asset data.
        self.assertEqual(4, len(output.lossassetdata_set))

        inserted_data = []

        for lad in output.lossassetdata_set:
            pos = lad.pos.coords(self.session)

            for curve in lad.losscurvedata_set:
                data = (Site(pos[0], pos[1]),
                        (Curve(zip(curve.abscissae, curve.poes)),
                        { u'assetID': lad.asset_id }))

                inserted_data.append(data)

        def normalize(values):
            result = []
            for value in values:
                result.append((value[0], (value[1][0], {
                    'assetID': value[1][1]['assetID']
                })))

            return sorted(result, key=lambda v: v[1][1]['assetID'])

        self.assertEquals(normalize(RISK_LOSS_CURVE_DATA), normalize(inserted_data))
