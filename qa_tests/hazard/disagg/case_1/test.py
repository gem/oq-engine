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

import StringIO
import numpy
import os
import shutil
import tempfile

from lxml import etree
from nose.plugins.attrib import attr

from openquake.nrmllib import PARSE_NS_MAP

from openquake.engine.db import models
from openquake.engine.export import hazard as haz_export

from qa_tests import _utils as qa_utils
from qa_tests.hazard.disagg.case_1 import _test_data as test_data

aac = lambda a, b: numpy.testing.assert_allclose(a, b, atol=5e-3)


class DisaggHazardCase1TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'disagg')
    def test(self):
        # TODO(LB): This is a temporary test case which tests for stability
        # until we can write proper QA tests.

        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')

        job = self.run_hazard(cfg)

        results = models.DisaggResult.objects.filter(output__oq_job=job)

        poe_002_pga = results.filter(imt='PGA', poe=0.02)
        rlz1, rlz2 = poe_002_pga.order_by('lt_realization')

        aac(test_data.RLZ_1_POE_002_PGA, rlz1.matrix)
        aac(test_data.RLZ_2_POE_002_PGA, rlz2.matrix)

        poe_002_sa = results.filter(imt='SA', poe=0.02)
        rlz1, rlz2 = poe_002_sa.order_by('lt_realization')

        aac(test_data.RLZ_1_POE_002_SA, rlz1.matrix)
        aac(test_data.RLZ_2_POE_002_SA, rlz2.matrix)

        poe_01_pga = results.filter(imt='PGA', poe=0.1)
        rlz1, rlz2 = poe_01_pga.order_by('lt_realization')

        aac(test_data.RLZ_1_POE_01_PGA, rlz1.matrix)
        aac(test_data.RLZ_2_POE_01_PGA, rlz2.matrix)

        poe_01_sa = results.filter(imt='SA', poe=0.1)
        rlz1, rlz2 = poe_01_sa.order_by('lt_realization')

        aac(test_data.RLZ_1_POE_01_SA, rlz1.matrix)
        aac(test_data.RLZ_2_POE_01_SA, rlz2.matrix)

        # Lastly, we should check an export of at least one of these results to
        # ensure that the disagg export/serialization is working properly.
        # The export isn't just a simple dump from the database; it requires
        # extraction of PMFs (Probability Mass Function) from a 6d matrix,
        # which are then serialized to XML.
        # This is not a trivial operation.
        try:
            target_dir = tempfile.mkdtemp()
            result_file = haz_export.export(rlz1.output.id, target_dir)
            expected = StringIO.StringIO(test_data.EXPECTED_XML_DISAGG)
            self.assert_disagg_xml_almost_equal(expected, result_file)
            self.assertTrue(qa_utils.validates_against_xml_schema(result_file))
        finally:
            shutil.rmtree(target_dir)

    def assert_disagg_xml_almost_equal(self, expected, actual):
        """
        A special helper function to test that values in the ``expected`` and
        ``actual`` XML are almost equal to a certain precision.

        :param expected, actual:
            Paths to XML files, or file-like objects containing the XML
            contents.
        """
        exp_tree = etree.parse(expected)
        act_tree = etree.parse(actual)

        # First, compare the <disaggMatrices> container element, check attrs,
        # etc.
        [exp_dms] = exp_tree.xpath(
            '//nrml:disaggMatrices', namespaces=PARSE_NS_MAP
        )
        [act_dms] = act_tree.xpath(
            '//nrml:disaggMatrices', namespaces=PARSE_NS_MAP
        )
        self.assertEqual(exp_dms.attrib, act_dms.attrib)

        # Then, loop over each <disaggMatrix>, check attrs, then loop over each
        # <prob> and compare indices and values.
        exp_dm = exp_tree.xpath(
            '//nrml:disaggMatrix', namespaces=PARSE_NS_MAP
        )
        act_dm = act_tree.xpath(
            '//nrml:disaggMatrix', namespaces=PARSE_NS_MAP
        )
        self.assertEqual(len(exp_dm), len(act_dm))

        for i, matrix in enumerate(exp_dm):
            act_matrix = act_dm[i]

            self.assertEqual(matrix.attrib['type'], act_matrix.attrib['type'])
            self.assertEqual(matrix.attrib['dims'], act_matrix.attrib['dims'])
            self.assertEqual(matrix.attrib['poE'], act_matrix.attrib['poE'])
            aac(float(act_matrix.attrib['iml']), float(matrix.attrib['iml']))

            # compare probabilities
            exp_probs = matrix.xpath('./nrml:prob', namespaces=PARSE_NS_MAP)
            act_probs = act_matrix.xpath(
                './nrml:prob', namespaces=PARSE_NS_MAP
            )
            self.assertEqual(len(exp_probs), len(act_probs))

            for j, prob in enumerate(exp_probs):
                act_prob = act_probs[j]

                self.assertEqual(prob.attrib['index'],
                                 act_prob.attrib['index'])
                aac(float(act_prob.attrib['value']),
                    float(prob.attrib['value']))
