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

# this is an example with 0 realization for source_model 1
# 5 realizations for source model 2
# (for TRT=Stable Shallow Crust) and 0 realizations
# for source model 3, i.e. a total of 5 realizations
EXPECTED_GMFS = [
    # (gsim_lt_path, gmf) pairs
    (['b2_1'],
     [0.0122635941118, 0.0139805763787, 0.0144103401398, 0.106379193896,
      0.0113950906248, 0.173096831205, 0.0284183447227, 0.0111461126959,
      0.0406849027044, 0.0425774398988, 0.0428851459108, 0.037313455383,
      0.0168288764889, 0.0502199069711, 0.00410128553024, 0.089528596683,
      0.320500228972, 0.0124056168978, 0.015956311957, 0.00523747290504,
      0.111933908976, 0.00536739363888, 0.00808594864775, 0.00171234002044,
      0.0201644415126, 0.010822649005, 0.010650141325, 0.00468375293726,
      0.00161591287534, 0.00320423188519]),
    (['b2_2'],
     [0.00488996441184, 0.00648086620305, 0.00598603781105, 0.0566560828959,
      0.00352564189752, 0.105686072301, 0.00966522094811, 0.00746870472411,
      0.0257385536403, 0.0578283232971, 0.0124026998092, 0.0134001180559,
      0.0125514300557, 0.0434876404699, 0.00347227954871, 0.0340441119578,
      0.0800200820967, 0.00501499831384, 0.00511291264323, 0.0011945513049,
      0.0534185176416, 0.00318663346798, 0.00557001608994, 0.00152530425326,
      0.0065566160049, 0.00389181044582, 0.00389991709715, 0.00338652733815,
      0.00091453570932, 0.000961338617142]),
    (['b2_3'],
     [0.0140430701358, 0.0146172496154, 0.0161965530977, 0.127170764721,
      0.0141347857456, 0.203635255114, 0.00921864206226, 0.0359156050092,
      0.0314702943179, 0.0346973609388, 0.0527125676158, 0.0139828934803,
      0.0411327578691, 0.00308496574929, 0.0467317319743, 0.108350578128,
      0.319890273816, 0.0138514581924, 0.0199551310723, 0.00680001151736,
      0.135513105726, 0.00430326482261, 0.00605077338281, 0.00114366190898,
      0.0258019694658, 0.0126173649689, 0.0125047231348, 0.00335979008973,
      0.00112720701386, 0.00350297539272]),
    (['b2_4'],
     [0.013383738924, 0.0165740680291, 0.0161629337318, 0.113232371809,
      0.0110511287076, 0.191411617978, 0.0210794887815, 0.0640203580921,
      0.116830394604, 0.0199843166908, 0.0325506814224, 0.0267521533035,
      0.0316587122966, 0.0942967424786, 0.0111786538056, 0.0819364976816,
      0.30458839682, 0.013904028016, 0.0152954926194, 0.00458674896471,
      0.11187900207, 0.0104801259334, 0.0161045487802, 0.00528614129664,
      0.0133255638176, 0.0115037374845, 0.011212645478, 0.0102900578847,
      0.00338649690623, 0.00337877976434]),
    (['b2_5'],
     [0.0132650156328, 0.0154189070193, 0.0154666588697, 0.127196918445,
      0.012993483865, 0.208249642139, 0.0205353527425, 0.0260804229817,
      0.07898663228, 0.140141740486, 0.0495611656051, 0.0288539784097,
      0.0400096024326, 0.0985081433425, 0.0123752012693, 0.105531435807,
      0.331924591203, 0.0131786723462, 0.0184732430141, 0.00598063504694,
      0.134147868775, 0.0153294489893, 0.0120091890011, 0.01406394966,
      0.00477935620563, 0.011807376867, 0.011672754981, 0.00961373237917,
      0.00365393122271, 0.00351445085014])
]


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
            self.assertEqual(len(actual_gmf), len(expected_gmf))
            numpy.testing.assert_almost_equal(
                sorted(actual_gmf), sorted(expected_gmf))
