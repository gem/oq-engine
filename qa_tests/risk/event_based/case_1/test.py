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

import os
import csv
import numpy

from nose.plugins.attrib import attr as noseattr

from qa_tests import risk
from tests.utils import helpers

from openquake.db import models


class EventBasedRiskCase1TestCase(risk.BaseRiskQATestCase):
    cfg = os.path.join(os.path.dirname(__file__), 'job.ini')

    EXPECTED_LOSS_CURVE_XML = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
</nrml>
    """

    EXPECTED_AGG_LOSS_CURVE_XML = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
</nrml>
    """

    EXPECTED_INS_LOSS_CURVE_XML = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
</nrml>
    """

    EXPECTED_LOSS_MAP_0_1_XML = """<?xml version='1.0' encoding='UTF-8'?>
</nrml>
    """

    EXPECTED_LOSS_MAP_0_2_XML = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
</nrml>"""

    EXPECTED_LOSS_MAP_0_5_XML = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
</nrml>
    """

    @noseattr('qa', 'risk', 'event_based')
    def test(self):
        self.run_test()

    def hazard_id(self):
        job = helpers.get_hazard_job(
            helpers.demo_file("event_based_hazard/job.ini"))

        hc = job.hazard_calculation

        gmf_set = models.GmfSet.objects.create(
            gmf_collection=models.GmfCollection.objects.create(
                output=models.Output.objects.create_output(
                    job, "Test Hazard output", "gmf"),
                    lt_realization=models.LtRealization.objects.create(
                        hazard_calculation=job.hazard_calculation,
                        ordinal=1, seed=1, weight=None,
                        sm_lt_path="test_sm", gsim_lt_path="test_gsim",
                        is_complete=False, total_items=1, completed_items=1),
                    complete_logic_tree_gmf=False),
                investigation_time=hc.investigation_time,
                ses_ordinal=1,
                complete_logic_tree_gmf=False)

        with open(os.path.join(
                os.path.dirname(__file__), 'gmf.csv'), 'rb') as csvfile:
            gmfreader = csv.reader(csvfile, delimiter=',')
            locations = gmfreader.next()

            for i, gmvs in enumerate(
                    numpy.array([[float(x) for x in row]
                                 for row in gmfreader]).transpose()):
                models.Gmf.objects.create(
                    gmf_set=gmf_set,
                    imt="PGA", gmvs=gmvs,
                    result_grp_ordinal=1,
                    location="POINT(%s)" % locations[i])

        return gmf_set.gmf_collection.output.id

    def actual_data(self, job):
        return ([curve.poes
                 for curve in models.LossCurveData.objects.filter(
                         loss_curve__output__oq_job=job,
                         loss_curve__aggregate=False,
                         loss_curve__insured=False).order_by('asset_ref')] +
                [curve.losses
                 for curve in models.LossCurveData.objects.filter(
                         loss_curve__output__oq_job=job,
                         loss_curve__aggregate=False,
                         loss_curve__insured=False).order_by('asset_ref')] +
                [curve.losses
                 for curve in models.LossCurveData.objects.filter(
                         loss_curve__output__oq_job=job,
                         loss_curve__aggregate=True,
                         loss_curve__insured=False).order_by('asset_ref')] +
                [curve.losses
                 for curve in models.LossCurveData.objects.filter(
                         loss_curve__output__oq_job=job,
                         loss_curve__aggregate=False,
                         loss_curve__insured=True).order_by('asset_ref')] +
                [point.value
                 for point in models.LossMapData.objects.filter(
                        loss_map__output__oq_job=job).order_by('asset_ref')])

    def expected_data(self):
        poes = [0, 0.0204, 0.0408, 0.0612, 0.0816, 0.102, 0.1224, 0.1429,
             0.1633, 0.1837, 0.2041, 0.2245, 0.2449, 0.2653, 0.2857,
             0.3061, 0.3265, 0.3469, 0.3673, 0.3878, 0.4082, 0.4286,
             0.449, 0.4694, 0.4898, 0.5102, 0.5306, 0.551, 0.5714,
             0.5918, 0.6122, 0.6327, 0.6531, 0.6735, 0.6939, 0.7143,
             0.7347, 0.7551, 0.7755, 0.7959, 0.8163, 0.8367, 0.8571,
             0.8776, 0.898, 0.9184, 0.9388, 0.9592, 0.9796, 1][::-1]

        losses_1 = [264.2259, 260.5148, 256.8037, 253.0926, 249.3815,
                    245.6704, 241.9593, 238.2482, 234.5371, 230.8261,
                    227.115, 223.4039, 219.6928, 215.9817, 212.2706,
                    208.5595, 204.8484, 201.1373, 197.4262, 193.7152,
                    190.0041, 186.293, 182.5819, 178.8708, 175.1597,
                    171.4486, 167.7375, 164.0264, 160.3153, 156.6043,
                    152.8932, 149.1393, 143.7887, 138.4381, 133.0875,
                    127.7369, 122.3862, 117.0356, 111.685, 106.3344,
                    100.9838, 95.6332, 90.2826, 85.5154, 81.0887,
                    76.662, 72.2353, 68.2291, 64.759, 34.233][::-1]
        return [
            poes, poes, poes,
            losses_1, [], [], [], [], [], [], None, None, None]

    def expected_outputs(self):
        return [self.EXPECTED_LOSS_CURVE_XML,
                self.EXPECTED_AGG_LOSS_CURVE_XML,
                self.EXPECTED_INS_LOSS_CURVE_XML,
                self.EXPECTED_LOSS_MAP_0_1_XML,
                self.EXPECTED_LOSS_MAP_0_2_XML,
                self.EXPECTED_LOSS_MAP_0_5_XML]
