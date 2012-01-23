# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


import unittest

from openquake.calculators.risk.event_based.core import (
    EventBasedRiskCalculator)

from tests.utils import helpers


class LossMapCurveSerialization(unittest.TestCase):

    def setUp(self):
        params = {
            'NUMBER_OF_SEISMICITY_HISTORIES': 0,
            'NUMBER_OF_LOGIC_TREE_SAMPLES': 0,
            'INVESTIGATION_TIME': 0.0,
            'OUTPUT_DIR': 'foo',
            'CALCULATION_MODE': 'Event Based',
            'BASE_PATH': '/tmp',
        }
        the_job = helpers.create_job(params)

        self.calculator = EventBasedRiskCalculator(the_job)
        the_job.serialize_results_to = ['db', 'xml']
        the_job.blocks_keys = []
        self.calculator.store_exposure_assets = lambda: None
        self.calculator.store_vulnerability_model = lambda: None
        self.calculator.partition = lambda: None

    def test_loss_map_serialized_if_conditional_loss_poes(self):
        self.calculator.calc_proxy.params['CONDITIONAL_LOSS_POE'] = (
            '0.01 0.02')

        with helpers.patch('openquake.calculators.risk.event_based.core'
                           '.plot_aggregate_curve'):
            with helpers.patch(
                'openquake.output.risk.create_loss_map_writer') as clw:

                clw.return_value = None

                self.calculator.execute()
                self.assertTrue(clw.called)

    def test_loss_map_not_serialized_unless_conditional_loss_poes(self):
        with helpers.patch('openquake.calculators.risk.event_based.core'
                           '.plot_aggregate_curve'):
            with helpers.patch(
                'openquake.output.risk.create_loss_map_writer') as clw:

                clw.return_value = None

                self.calculator.execute()
                self.assertFalse(clw.called)
