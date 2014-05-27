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

import os

import numpy

from nose.plugins.attrib import attr
from openquake.engine.db import models
from qa_tests import _utils as qa_utils

GET_GMF_OUTPUTS = '''
select gsim_lt_path, n, avg, std from hzrdr.gmf_stats as a,
hzrdr.lt_realization as b, hzrdr.gmf as c
where lt_realization_id=b.id and gmf_id=c.id
and a.output_id=c.output_id and a.output_id in
(select id from uiapi.output where oq_job_id=%s and output_type='gmf')
order by a.output_id;
'''

# this is an example with 4 realizations for source_model 1,
# 0 realization for source model 2 and 0 realizations
# for source model 3, i.e. a total of 4 realizations
EXPECTED_GMFS = [
    (['b1_1'], 2, 0.002508579548775, 0.00126274496868308),
    (['b1_2'], 2, 0.0009968459584405, 0.000610752894244364),
    (['b1_3'], 2, 0.00174022255931, 0.000987838801570935),
    (['b1_4'], 2, 0.002654602993195, 0.00140628294771318)]


class EventBasedHazardCase5TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
        job = self.run_hazard(cfg)
        cursor = models.getcursor('job_init')
        cursor.execute(GET_GMF_OUTPUTS % job.id)
        actual_gmfs = cursor.fetchall()
        self.assertEqual(len(actual_gmfs), len(EXPECTED_GMFS))
        for a, e in zip(actual_gmfs, EXPECTED_GMFS):
            self.assertEqual(a[0], e[0])
            numpy.testing.assert_almost_equal(a[1:], e[1:])
