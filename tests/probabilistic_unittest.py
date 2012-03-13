# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


import unittest

from openquake import engine
from openquake.calculators.risk.event_based.core import (
    EventBasedRiskCalculator)

from tests.utils import helpers


class LossMapCurveSerialization(unittest.TestCase):

    def setUp(self):
        cfg_path = helpers.demo_file(
            'probabilistic_event_based_risk/config.gem')

        job = engine.prepare_job()
        jp, params, sections = engine.import_job_profile(cfg_path, job)

        job_ctxt = engine.JobContext(
            params, 1, sections=sections, base_path='/tmp',
            serialize_results_to=['db', 'xml'], oq_job_profile=jp, oq_job=job)
        job_ctxt.blocks_keys = []

        self.calculator = EventBasedRiskCalculator(job_ctxt)
        self.calculator.store_exposure_assets = lambda: None
        self.calculator.store_vulnerability_model = lambda: None
        self.calculator.partition = lambda: None

    def test_loss_map_serialized_if_conditional_loss_poes(self):
        self.calculator.job_ctxt.params['CONDITIONAL_LOSS_POE'] = (
            '0.01 0.02')

        with helpers.patch(
            'openquake.output.risk.create_loss_map_writer') as clw:

            clw.return_value = None

            self.calculator.execute()
            self.calculator.post_execute()
            self.assertTrue(clw.called)

    def test_loss_map_not_serialized_unless_conditional_loss_poes(self):
        with helpers.patch(
            'openquake.output.risk.create_loss_map_writer') as clw:

            clw.return_value = None

            self.calculator.execute()
            self.assertFalse(clw.called)
