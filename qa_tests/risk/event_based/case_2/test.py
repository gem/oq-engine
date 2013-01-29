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


class EventBasedRiskCase2TestCase(risk.BaseRiskQATestCase):
    cfg = os.path.join(os.path.dirname(__file__), 'job.ini')

    EXPECTED_LOSS_CURVE_XML = """<?xml version='1.0' encoding='UTF-8'?>
    <nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">\n  <lossCurves investigationTime="50.0" sourceModelTreePath="test_sm" gsimTreePath="test_gsim" unit="USD">\n    <lossCurve assetRef="a1">\n      <gml:Point>\n        <gml:pos>15.48 38.09</gml:pos>\n      </gml:Point>\n      <poEs>1.0 0.875 0.75 0.625 0.5 0.375 0.25 0.125 0.0</poEs>\n      <losses>34.3158848505 85.3993696079 117.245425502 149.043885673 172.193230479 195.342575284 218.49192009 241.641264896 264.790609701</losses>\n      <lossRatios>0.0114386282835 0.028466456536 0.0390818085005 0.0496812952244 0.057397743493 0.0651141917615 0.07283064003 0.0805470882986 0.0882635365671</lossRatios>\n    </lossCurve>\n    <lossCurve assetRef="a2">\n      <gml:Point>\n        <gml:pos>15.56 38.17</gml:pos>\n      </gml:Point>\n      <poEs>1.0 0.875 0.75 0.625 0.5 0.375 0.25 0.125 0.0</poEs>\n      <losses>8.76706068558 30.247789599 30.8360122117 31.1984360597 31.2782554554 31.3580748512 31.4378942469 31.5177136427 31.5975330384</losses>\n      <lossRatios>0.00438353034279 0.0151238947995 0.0154180061058 0.0155992180298 0.0156391277277 0.0156790374256 0.0157189471235 0.0157588568213 0.0157987665192</lossRatios>\n    </lossCurve>\n    <lossCurve assetRef="a3">\n      <gml:Point>\n        <gml:pos>15.48 38.25</gml:pos>\n      </gml:Point>\n      <poEs>1.0 0.875 0.75 0.625 0.5 0.375 0.25 0.125 0.0</poEs>\n      <losses>11.5144783375 34.5514270991 39.0887926791 43.4302192561 44.7861535336 46.1420878111 47.4980220885 48.853956366 50.2098906434</losses>\n      <lossRatios>0.0115144783375 0.0345514270991 0.0390887926791 0.0434302192561 0.0447861535336 0.0461420878111 0.0474980220885 0.048853956366 0.0502098906434</lossRatios>\n    </lossCurve>\n  </lossCurves>\n</nrml>
    """

    EXPECTED_AGG_LOSS_CURVE_XML = """<?xml version='1.0' encoding='UTF-8'?>
    <nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">\n  <aggregateLossCurve investigationTime="50.0" sourceModelTreePath="test_sm" gsimTreePath="test_gsim" unit="USD">\n    <poEs>1.0 0.875 0.75 0.625 0.5 0.375 0.25 0.125 0.0</poEs>\n    <losses>55.0411 157.5215 191.8946 222.8025 244.5078 266.2131 287.9184 309.6237 331.3290</losses>\n  </aggregateLossCurve>\n</nrml>\n"""

    @noseattr('qa', 'risk', 'event_based')
    def test(self):
        self._run_test()

    def hazard_id(self):
        job = helpers.get_hazard_job(
            helpers.demo_file("event_based_hazard/job.ini"))

        job.hazard_calculation = models.HazardCalculation.objects.create(
            owner=job.hazard_calculation.owner,
            truncation_level=job.hazard_calculation.truncation_level,
            maximum_distance=job.hazard_calculation.maximum_distance,
            intensity_measure_types_and_levels=(
                job.hazard_calculation.intensity_measure_types_and_levels),
            calculation_mode="event_based",
            investigation_time=50,
            ses_per_logic_tree_path=1)
        job.save()
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
                for curve in models.AggregateLossCurveData.objects.filter(
                    loss_curve__output__oq_job=job,
                    loss_curve__aggregate=True,
                    loss_curve__insured=False)])

    def expected_data(self):

        poes = [1., 0.875, 0.75, 0.625, 0.5, 0.375, 0.25, 0.125, 0.]

        losses_1 = [34.3158848505, 85.3993696079, 117.245425502,
                    149.043885673, 172.193230479, 195.342575284, 218.49192009,
                    241.641264896, 264.790609701]

        losses_2 = [8.76706068558, 30.247789599, 30.8360122117,
                    31.1984360597, 31.2782554554, 31.3580748512, 31.4378942469,
                    31.5177136427, 31.5975330384]

        losses_3 = [11.5144783375, 34.5514270991, 39.0887926791,
                    43.4302192561, 44.7861535336, 46.1420878111,
                    47.4980220885, 48.853956366, 50.2098906434]

        expected_aggregate_losses = [55.0410853535, 157.521455945,
                                     191.894562028, 222.802501033,
                                     244.507808584, 266.213116134,
                                     287.918423685, 309.623731235,
                                     331.329038786]

        return [poes, poes, poes, losses_1, losses_2, losses_3,
                expected_aggregate_losses]

    def expected_outputs(self):
        return [self.EXPECTED_LOSS_CURVE_XML, self.EXPECTED_AGG_LOSS_CURVE_XML]
