# Copyright (c) 2010-2014, GEM Foundation.
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

import csv
import numpy
import unittest
import os
import shutil
import filecmp

from nose.plugins.attrib import attr

from openquake.commonlib.nrml import PARSE_NS_MAP
from openquake.engine.db import models

from lxml import etree

from openquake.engine.tests.utils import helpers


class BaseQATestCase(unittest.TestCase):
    """
    Base QA test case class with some general functionality built in for
    running QA tests.
    """

    def run_hazard(self, cfg, exports=''):
        """
        Given the path to job config file, run the job and assert that it was
        successful. If this assertion passes, return the completed job.

        :param str cfg:
            Path to a job config file.
        :returns:
            The completed :class:`~openquake.engine.db.models.OqJob`.
        :raises:
            :exc:`AssertionError` if the job was not successfully run.
        """
        completed_job = helpers.run_job(cfg, exports=exports).job
        self.assertEqual('complete', completed_job.status)

        return completed_job

    def assert_xml_equal(self, a, b):
        """
        Compare two XML artifacts for equality.

        :param a, b:
            Paths to XML files, or a file-like object containing the XML
            contents.
        """
        contents_a = etree.tostring(etree.parse(a), pretty_print=True)
        contents_b = etree.tostring(etree.parse(b), pretty_print=True)

        self.assertEqual(contents_a, contents_b)

    def assert_equals_var_tolerance(self, expected, actual):
        """
        Assert (almost) equal with a variable tolerance. For extremely low
        values (< 0.0005), tolerance is 3 digits. For everything >= 0.0005,
        tolerance is 2 digits.
        """
        for i, exp in enumerate(expected):
            act = actual[i]

            if exp < 0.0005:
                tolerance = 3
            else:
                tolerance = 2
            numpy.testing.assert_almost_equal(act, exp, decimal=tolerance)


def compare_hazard_curve_with_csv(
        job, sm_lt_path, gsim_lt_path, imt, sa_period, sa_damping,
        csv_name, csv_delimiter, rtol):
    """
    This is useful in tests that compares the hazard curves in the db with
    the expected values in the csv. The csv is expected to have the form
    `lon, lat, poe1, poe2, ...`
    """
    rlzs = list(
        models.LtRealization.objects.filter(lt_model__hazard_calculation=job))
    # there is some contorsion here since is seems that Django filtering
    # with CharArrayFields does not work, so I get all the realizations
    # and I extract by hand the one with the given lt_paths
    [rlz] = [r for r in rlzs
             if r.sm_lt_path == sm_lt_path
             and r.gsim_lt_path == gsim_lt_path]
    curves = models.HazardCurveData.objects.filter(
        hazard_curve__lt_realization=rlz,
        hazard_curve__imt=imt,
        hazard_curve__sa_period=sa_period,
        hazard_curve__sa_damping=sa_damping)

    data = []  # read computed data from db
    for hazard_curve_data in curves:
        loc = hazard_curve_data.location
        data.append([loc.x, loc.y] + hazard_curve_data.poes)
    data.sort()  # expects the csv values to be sorted by lon, lat

    # read expected data from csv
    with open(csv_name) as f:
        reader = csv.reader(f, delimiter=csv_delimiter)
        expected_data = [map(float, row) for row in reader]

    try:
        numpy.testing.assert_allclose(expected_data, data, rtol=rtol)
    except:
        # to debug the test, in case it breaks, comment the assert and
        # uncomment the following, lines then compare the expected file with
        # the file generated from the computed data and stored in /tmp:
        #import os
        #tmp = os.path.join('/tmp', os.path.basename(csv_name))
        #print 'saving', tmp
        #print >>open(tmp, 'w'), '\n'.join(' '.join(map(str, r)) for r in data)
        raise

aac = lambda a, b: numpy.testing.assert_allclose(a, b, atol=1e-5)


class DisaggHazardTestCase(BaseQATestCase):
    fnames = []  # to be overridden
    working_dir = os.path.dirname(__file__)
    imts = []

    @attr('qa', 'hazard', 'disagg')
    def test(self):
        cfg = os.path.join(self.working_dir, 'job.ini')
        expected = os.path.join(self.working_dir, 'expected_output')
        job = self.run_hazard(cfg, exports='xml')
        export_dir = os.path.join(
            job.get_param('export_dir'), 'calc_%d' % job.id)

        # compare the directories and print a report
        dc = filecmp.dircmp(expected, export_dir)
        dc.report_full_closure()

        # compare the disagg files
        for fname in self.fnames:
            for imt in self.imts:
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
