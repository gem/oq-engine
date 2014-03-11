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
import filecmp

from lxml import etree
from nose.plugins.attrib import attr

from openquake.nrmllib import PARSE_NS_MAP

from qa_tests import _utils

aac = lambda a, b: numpy.testing.assert_allclose(a, b, atol=1e-5)


fnames = [
    'disagg_matrix(0.02)-lon_10.1-lat_40.1-smltp_b1-gsimltp_b1-ltr_0.xml',
    'disagg_matrix(0.02)-lon_10.1-lat_40.1-smltp_b1-gsimltp_b1-ltr_1.xml',
    'disagg_matrix(0.1)-lon_10.1-lat_40.1-smltp_b1-gsimltp_b1-ltr_0.xml',
    'disagg_matrix(0.1)-lon_10.1-lat_40.1-smltp_b1-gsimltp_b1-ltr_1.xml']


class DisaggHazardCase1TestCase(_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'disagg')
    def test(self):
        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
        expected = os.path.join(os.path.dirname(__file__), 'expected_output')
        job = self.run_hazard(cfg, exports=['xml'])
        hc = job.hazard_calculation
        export_dir = os.path.join(hc.export_dir, 'calc_%d' % hc.id)

        # compare the directories and print a report
        dc = filecmp.dircmp(expected, export_dir)
        dc.report_full_closure()

        # compare the disagg files
        for fname in fnames:
            for imt in ('PGA', 'SA-0.025'):
                exp = os.path.join(expected, 'disagg_matrix', imt, fname)
                got = os.path.join(export_dir, 'disagg_matrix', imt, fname)
                self.assert_disagg_xml_almost_equal(exp, got)

        # remove the export_dir if the test passes
        shutil.rmtree(export_dir)

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
