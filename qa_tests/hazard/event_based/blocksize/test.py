# Copyright (c) 2013, GEM Foundation.
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
from nose.plugins.attrib import attr
from qa_tests import _utils as qa_utils
from openquake.engine.db import models

from openquake.engine.calculators.hazard.event_based.core import \
    EventBasedHazardCalculator


# test independence from the parameter concurrent_tasks
# it is using a source model with 398 sources and a single SES
class EventBasedHazardTestCase(qa_utils.BaseQATestCase):
    DEBUG = False
    # if the test fails and you want to debug it, set this flag:
    # then you will see in /tmp a few files which you can diff
    # to see the problem
    expected_tags = ['rlz=00|ses=0001|src=1|i=000',
                     'rlz=00|ses=0001|src=1|i=001',
                     'rlz=00|ses=0001|src=1|i=002',
                     'rlz=00|ses=0001|src=1|i=003',
                     'rlz=00|ses=0001|src=1|i=004',
                     'rlz=00|ses=0001|src=1|i=005',
                     'rlz=00|ses=0001|src=2|i=000']
    expected_gmfs = '''\
GMFsPerSES(investigation_time=50.000000, stochastic_event_set_id=1,
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=rlz=00|ses=0001|src=1|i=000
<X=131.00000, Y= 40.10000, GMV=0.0018425>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=rlz=00|ses=0001|src=1|i=001
<X=131.00000, Y= 40.00000, GMV=0.0036347>
<X=131.00000, Y= 40.10000, GMV=0.0040173>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=rlz=00|ses=0001|src=1|i=002
<X=131.00000, Y= 40.00000, GMV=0.0071390>
<X=131.00000, Y= 40.10000, GMV=0.0106517>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=rlz=00|ses=0001|src=1|i=003
<X=131.00000, Y= 40.00000, GMV=0.0043736>
<X=131.00000, Y= 40.10000, GMV=0.0171066>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=rlz=00|ses=0001|src=1|i=004
<X=131.00000, Y= 40.00000, GMV=0.0032255>
<X=131.00000, Y= 40.10000, GMV=0.0029204>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=rlz=00|ses=0001|src=1|i=005
<X=131.00000, Y= 40.00000, GMV=0.0166739>
<X=131.00000, Y= 40.10000, GMV=0.0080238>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=rlz=00|ses=0001|src=2|i=000
<X=131.00000, Y= 40.00000, GMV=0.0056535>
<X=131.00000, Y= 40.10000, GMV=0.0016968>))'''

    @attr('qa', 'hazard', 'event_based')
    def test_64(self):
        tags_64, gmfs_64 = self.run_with_concurrent_tasks(64)
        self.assertEqual(tags_64, self.expected_tags)
        if self.DEBUG:  # write the output on /tmp so you can diff it
            open('/tmp/64-got.txt', 'w').write(gmfs_64)
            open('/tmp/64-exp.txt', 'w').write(self.expected_gmfs)
        self.assertEqual(gmfs_64, self.expected_gmfs)

    def test_32(self):
        tags_32, gmfs_32 = self.run_with_concurrent_tasks(32)
        self.assertEqual(tags_32, self.expected_tags)
        if self.DEBUG:  # write the output on /tmp so you can diff it
            open('/tmp/32-got.txt', 'w').write(gmfs_32)
            open('/tmp/32-exp.txt', 'w').write(self.expected_gmfs)
        self.assertEqual(gmfs_32, self.expected_gmfs)

    def run_with_concurrent_tasks(self, n):
        orig = EventBasedHazardCalculator.concurrent_tasks.im_func
        EventBasedHazardCalculator.concurrent_tasks = lambda self: n
        try:
            cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
            job = self.run_hazard(cfg)
            tags = models.SESRupture.objects.filter(
                ses__ses_collection__output__oq_job=job
                ).values_list('tag', flat=True)
            # gets the GMFs for all the ruptures in the only existing SES
            [gmfs_per_ses] = list(models.Gmf.objects.get(output__oq_job=job))
        finally:
            EventBasedHazardCalculator.concurrent_tasks = orig
        return map(str, tags), str(gmfs_per_ses)
