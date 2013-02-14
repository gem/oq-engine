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

import openquake.nrmllib
import unittest

import openquake.engine

from lxml import etree
from mock import patch
from numpy import median

from tests.utils import helpers
from openquake.engine.db import models


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
        # Set OQ_NO_DISTRIBUTE to true, so we can benefit from including these
        # tests in our code coverage
        with patch.dict('os.environ',
                        {openquake.engine.NO_DISTRIBUTE_VAR: '1'}):
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


def validates_against_xml_schema(
        xml_instance_path, schema_path=openquake.nrmllib.nrml_schema_file()):
    """
    Check whether an XML file validates against an XML schema.
    """
    xml_doc = etree.parse(xml_instance_path)
    xmlschema = etree.XMLSchema(etree.parse(schema_path))
    return xmlschema.validate(xml_doc)


def get_gmfs_per_site(output, imt):
    for gmf in models.get_gmfs_scenario(output, imt):
        yield [gmfnode.gmv for gmfnode in gmf]


def get_medians(output, imt):
    """
    Compute the median of ground motion fields on a per site basis.
    """
    for gmfs in get_gmfs_per_site(output, imt):
        yield median(gmfs)  # don't use a genexp


def count(gmf_value, gmfs_site_one, gmfs_site_two,
          delta_prob=0.1, div_factor=2.0):
    """
    Count the number of pairs of gmf values
    within the specified range.
    See https://bugs.launchpad.net/openquake/+bug/1097646
    attached Scenario Hazard script.
    """

    count = 0
    lower_bound = gmf_value - delta_prob / div_factor
    upper_bound = gmf_value + delta_prob / div_factor

    for v1, v2 in zip(gmfs_site_one, gmfs_site_two):
        if ((lower_bound <= v1 <= upper_bound) and
                (lower_bound <= v2 <= upper_bound)):
            count += 1
    return count
