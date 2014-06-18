# Copyright (c) 2014, GEM Foundation.
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

"""
This is a fast test of the event_loss_table, which is quite stringent
"""
import collections
from nose.plugins.attrib import attr as noseattr
from qa_tests import risk

from openquake.engine.db import models


class EventBaseQATestCase1(risk.CompleteTestCase, risk.FixtureBasedQATestCase):
    hazard_calculation_fixture = "PEB QA test 2"

    @noseattr('qa', 'risk', 'event_based')
    def test(self):
        self._run_test()

    expected_elt = [
        ('smlt=00|ses=0019|src=3|rup=004-01', 6.15, 3087.69243118),
        ('smlt=00|ses=0006|src=1|rup=004-01', 6.15, 2400.379029),
        ('smlt=00|ses=0004|src=1|rup=003-01', 5.85, 1451.10749075),
        ('smlt=00|ses=0019|src=1|rup=004-01', 6.15, 1236.87701359),
        ('smlt=00|ses=0013|src=1|rup=003-01', 5.85, 1186.2710497),
        ('smlt=00|ses=0016|src=2|rup=005-01', 6.45, 1120.1768802),
        ('smlt=00|ses=0018|src=2|rup=001-01', 5.25, 1120.08595039),
        ('smlt=00|ses=0005|src=2|rup=001-01', 5.25, 1119.98450891),
        ('smlt=00|ses=0013|src=2|rup=001-01', 5.25, 1074.88832758),
        ('smlt=00|ses=0005|src=3|rup=002-01', 5.55, 591.850172435),
        ('smlt=00|ses=0018|src=3|rup=001-01', 5.25, 517.768258334),
        ('smlt=00|ses=0015|src=2|rup=001-01', 5.25, 217.751093258),
        ('smlt=00|ses=0003|src=1|rup=001-01', 5.25, 204.770676989),
        ('smlt=00|ses=0003|src=1|rup=001-02', 5.25, 199.374461766),
        ('smlt=00|ses=0009|src=2|rup=005-01', 6.45, 137.719501569),
        ('smlt=00|ses=0011|src=2|rup=002-01', 5.55, 124.731722658),
        ('smlt=00|ses=0018|src=2|rup=001-03', 5.25, 117.308215526),
        ('smlt=00|ses=0003|src=2|rup=001-01', 5.25, 96.5702659374),
        ('smlt=00|ses=0018|src=2|rup=001-02', 5.25, 71.8709085026),
    ]

    expected_loss_fractions = collections.OrderedDict([
        ('80.0000,82.0000|28.0000,30.0000',
         (4050.860981516, 0.6065271127743204)),
        ('82.0000,84.0000|26.0000,28.0000',
         (1186.2710497, 0.17761793308271825)),
        ('84.0000,86.0000|26.0000,28.0000',
         (1441.647690579, 0.21585495414296138)),
    ])

    def check_event_loss_table(self, job):
        # we check only the first 10 values of the event loss table
        # for loss_type=structural and branch b2
        el = models.EventLoss.objects.get(
            output__output_type='event_loss', output__oq_job=job)
        elt = el.eventlossdata_set.order_by('-aggregate_loss')

        for e, row in zip(elt, self.expected_elt):
            self.assertEqual(e.rupture.tag, row[0])
            self.assertEqual(e.rupture.rupture.mag, row[1])
            self.assertAlmostEqual(e.aggregate_loss, row[2])

    def check_loss_fraction(self, job):
        [fractions] = models.LossFraction.objects.filter(
            output__oq_job=job, variable="coordinate",
            loss_type='structural').order_by('hazard_output')
        site, odict = fractions.iteritems().next()
        # the disaggregation site in job_risk.ini
        self.assertEqual(site, (81.2985, 29.1098))
        self.assertEqual(odict, self.expected_loss_fractions)
