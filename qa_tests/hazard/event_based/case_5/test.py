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
# 1 realization for source model 2 and 0 realizations
# for source model 3, i.e. a total of 5 realizations
EXPECTED_GMFS = [
    (['b1_1'], 363, 0.00199170566738161, 0.00144512913080544),
    (['b1_2'], 363, 0.00111575899610696, 0.00109450082421796),
    (['b1_3'], 363, 0.00117661171359837, 0.00100375543117846),
    (['b1_4'], 363, 0.00193367922840302, 0.00148667206555683),
    (['b4_1'], 1900, 0.00435749544458869, 0.0100415828332556)]


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
