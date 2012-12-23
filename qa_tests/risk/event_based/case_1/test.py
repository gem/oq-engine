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

        with open('gmf.csv', 'rb') as csvfile:
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

        return gmf_set.gmfcollection.output.id

    def actual_data(self, job):
        return ([curve.loss_ratios
                for curve in models.LossCurveData.objects.filter(
                        loss_curve__output__oq_job=job,
                        loss_curve__aggregate=False,
                        loss_curve__insured=False).order_by('asset_ref')] +
                [curve.loss_ratios
                for curve in models.LossCurveData.objects.filter(
                        loss_curve__output__oq_job=job,
                        loss_curve__aggregate=True,
                        loss_curve__insured=False).order_by('asset_ref')] +
                [curve.loss_ratios
                for curve in models.LossCurveData.objects.filter(
                        loss_curve__output__oq_job=job,
                        loss_curve__aggregate=False,
                        loss_curve__insured=True).order_by('asset_ref')] +
                [point.value
                 for point in models.LossMapData.objects.filter(
                        loss_map__output__oq_job=job).order_by('asset_ref')])

    def expected_data(self):
        return [[], None, None, None]

    def expected_outputs(self):
        return [self.EXPECTED_LOSS_CURVE_XML,
                self.EXPECTED_AGG_LOSS_CURVE_XML,
                self.EXPECTED_INS_LOSS_CURVE_XML,
                self.EXPECTED_LOSS_MAP_0_1_XML,
                self.EXPECTED_LOSS_MAP_0_2_XML,
                self.EXPECTED_LOSS_MAP_0_5_XML]
