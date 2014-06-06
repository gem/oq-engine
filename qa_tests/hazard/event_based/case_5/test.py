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
select gsim_lt_path, array_concat(gmvs order by site_id, task_no) as gmf
from hzrdr.gmf_data as a, hzrdr.lt_realization as b, hzrdr.gmf as c
where lt_realization_id=b.id and a.gmf_id=c.id and c.output_id in
(select id from uiapi.output where oq_job_id=%d and output_type='gmf')
group by gsim_lt_path, c.output_id, imt, sa_period, sa_damping
order by c.output_id;
'''

# this is an example with 1 realization for source_model 1
# (for TRT=Volcanic), 5 realizations for source model 2
# (for TRT=Stable Shallow Crust) and 0 realizations
# for source model 3, i.e. a total of 6 realizations
EXPECTED_GMFS = [
    # (gsim_lt_path, gmf) pairs
    (['b4_1'], [0.00358084915845, 0.00721057851016, 0.00273325202693,
                0.000505733453409, 0.0054940388042, 0.0108615164622,
                0.00210492862451, 0.00795157407803]),
    (['b2_1'], [0.00758690593265, 0.00389381998647, 0.0130433056525,
                0.00760062124467, 0.0163181512477, 0.0144237039008,
                0.0125792721737, 0.07347413695, 0.0467792700799]),
    (['b2_2'], [0.00367067364985, 0.00176210792132, 0.00895550038364,
                0.00338078563361, 0.0121254368508, 0.00963232905743,
                0.00715191928051, 0.0748774290918, 0.038855640027]),
    (['b2_3'], [0.00855261393654, 0.00423526643358, 0.0119960332245,
                0.00710298021251, 0.014954360278, 0.0136637476071,
                0.0136130922009, 0.0640468400481, 0.044230781953]),
    (['b2_4'], [0.00942913934082, 0.00475877688936, 0.0202980209034,
                0.0108229080694, 0.026156828175, 0.0223459674633,
                0.0169413815865, 0.142953300825, 0.0806493233057]),
    (['b2_5'], [0.0139470915443, 0.00644178768174, 0.0193342487453,
                0.0102465096233, 0.0229512441944, 0.0209073720926,
                0.0224156055477, 0.103859718741, 0.073263981492])]


class EventBasedHazardCase5TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
        job = self.run_hazard(cfg)
        cursor = models.getcursor('job_init')
        cursor.execute(GET_GMF_OUTPUTS % job.id)
        actual_gmfs = cursor.fetchall()
        self.assertEqual(len(actual_gmfs), len(EXPECTED_GMFS))
        for (actual_path, actual_gmf), (expected_path, expected_gmf) in zip(
                actual_gmfs, EXPECTED_GMFS):
            self.assertEqual(actual_path, expected_path)
            numpy.testing.assert_almost_equal(actual_gmf, expected_gmf)
