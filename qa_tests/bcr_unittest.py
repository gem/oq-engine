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
import shutil
import unittest

from lxml import etree
from nose.plugins.attrib import attr

from openquake.db.models import OqCalculation
from openquake.nrml import nrml_schema_file

from tests.utils import helpers


BCR_DEMO_BASE = 'demos/benefit_cost_ratio'


CONFIG = '%s/config.gem' % BCR_DEMO_BASE
COMPUTED_OUTPUT = '%s/computed_output' % BCR_DEMO_BASE
RESULT = '%s/bcr-map.xml' % COMPUTED_OUTPUT

NRML = 'http://openquake.org/xmlns/nrml/0.3'
GML = 'http://www.opengis.net/gml'


class BCRQATestCase(unittest.TestCase):

    # TODO: fix the code and remove @skipit
    @helpers.skipit
    @attr('qa')
    def test_bcr(self):
        expected_result = {
        #    site location
            (-122.0, 38.225): {
                # assetRef  eal_orig  eal_retrof  bcr
                    'a1':   (0.00838,  0.00587,  0.43405)
            }
        }
        delta = 1e-5

        helpers.run_job(CONFIG)
        job_record = OqCalculation.objects.latest("id")
        self.assertEqual('succeeded', job_record.status)

        result = self._parse_bcr_map(RESULT)
        try:
            helpers.assertDeepAlmostEqual(self, expected_result, result,
                                          delta=delta)
        finally:
            shutil.rmtree(COMPUTED_OUTPUT)


    def _parse_bcr_map(self, filename):
        self.assertTrue(os.path.exists(filename))
        schema = etree.XMLSchema(file=nrml_schema_file())
        parser = etree.XMLParser(schema=schema)
        tree = etree.parse(filename, parser=parser)

        bcrnodes = tree.getroot().findall(
            '{%(ns)s}riskResult/{%(ns)s}benefitCostRatioMap/{%(ns)s}BCRNode' %
            {'ns': NRML}
        )
        result = {}

        for bcrnode in bcrnodes:
            [site] = bcrnode.findall('{%s}site/{%s}Point/{%s}pos' %
                                     (NRML, GML, GML))
            assets = {}
            valuenodes = bcrnode.findall('{%s}benefitCostRatioValue' % NRML)
            for valuenode in valuenodes:
                values = []
                for tag in ('expectedAnnualLossOriginal',
                            'expectedAnnualLossRetrofitted',
                            'benefitCostRatio'):
                    [node] = valuenode.findall('{%s}%s' % (NRML, tag))
                    values.append(float(node.text))
                assets[valuenode.attrib['assetRef']] = tuple(values)
            result[tuple(map(float, site.text.split()))] = assets

        return result
