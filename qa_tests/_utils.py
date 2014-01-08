# Copyright (c) 2010-2013, GEM Foundation.
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

import openquake.engine
import openquake.nrmllib
from openquake.engine.db import models

from lxml import etree

from openquake.engine.tests.utils import helpers


class BaseQATestCase(unittest.TestCase):
    """
    Base QA test case class with some general functionality built in for
    running QA tests.
    """

    def run_hazard(self, cfg, exports=None):
        """
        Given the path to job config file, run the job and assert that it was
        successful. If this assertion passes, return the completed job.

        :param str cfg:
            Path to a job config file.
        :param list exports:
            A list of export format types. Currently only 'xml' is supported.
        :returns:
            The completed :class:`~openquake.engine.db.models.OqJob`.
        :raises:
            :exc:`AssertionError` if the job was not successfully run.
        """
        completed_job = helpers.run_hazard_job(cfg, exports=exports)
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


def validates_against_xml_schema(
        xml_instance_path, schema_path=openquake.nrmllib.nrml_schema_file()):
    """
    Check whether an XML file validates against an XML schema.
    """
    xml_doc = etree.parse(xml_instance_path)
    xmlschema = etree.XMLSchema(etree.parse(schema_path))
    return xmlschema.validate(xml_doc)


def count(gmf_value, gmfs_site_one, gmfs_site_two,
          delta_prob=0.1, div_factor=2.0):
    """
    Count the number of pairs of gmf values
    within the specified range.
    See https://bugs.launchpad.net/openquake/+bug/1097646
    attached Scenario Hazard script.
    """

    i = 0
    lower_bound = gmf_value - delta_prob / div_factor
    upper_bound = gmf_value + delta_prob / div_factor

    for v1, v2 in zip(gmfs_site_one, gmfs_site_two):
        if ((lower_bound <= v1 <= upper_bound) and
                (lower_bound <= v2 <= upper_bound)):
            i += 1
    return i


def compare_hazard_curve_with_csv(
        hc, sm_lt_path, gsim_lt_path, imt, sa_period, sa_damping,
        csv_name, csv_delimiter, rtol):
    """
    This is useful in tests that compares the hazard curves in the db with
    the expected values in the csv. The csv is expected to have the form
    `lon, lat, poe1, poe2, ...`
    """
    rlzs = list(models.LtRealization.objects.filter(hazard_calculation=hc))
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

    numpy.testing.assert_allclose(expected_data, data, rtol=rtol)
    # to debug the test, in case it breaks, comment the assert and
    # uncomment the following, lines then compare the expected file with
    # the file generated from the computed data and stored in /tmp:
    # import os
    # tmp = os.path.join('/tmp', os.path.basename(csv_name))
    # print 'saving', tmp
    # print >> open(tmp, 'w'), '\n'.join(' '.join(map(str, r)) for r in data)
