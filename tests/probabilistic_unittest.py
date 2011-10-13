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


import mock
import unittest

from openquake.risk.job.probabilistic import ProbabilisticEventMixin

from tests.utils.helpers import patch


NUMBER_OF_SAMPLES_FROM_CONFIG = "10"


class SamplesFromConfigTestCase(unittest.TestCase):
    """Tests for the functionality that reads the number of samples
    for the probabilistic scenario from the configuration file."""

    def setUp(self):
        self.mixin = ProbabilisticEventMixin()

    def test_without_parameter_we_use_the_default_value(self):
        self.assertEqual(None, self.mixin._get_number_of_samples())

    def test_with_empty_parameter_we_use_the_default_value(self):
        self.mixin.__dict__["PROB_NUM_OF_SAMPLES"] = ""
        self.assertEqual(None, self.mixin._get_number_of_samples())

    def test_we_use_the_parameter_when_specified(self):
        self.mixin.__dict__["PROB_NUM_OF_SAMPLES"] = \
                NUMBER_OF_SAMPLES_FROM_CONFIG

        self.assertEqual(int(NUMBER_OF_SAMPLES_FROM_CONFIG),
                         self.mixin._get_number_of_samples())

    def test_default_value_with_wrong_parameter(self):
        self.mixin.__dict__["PROB_NUM_OF_SAMPLES"] = "this-is-wrong"
        self.assertEqual(None, self.mixin._get_number_of_samples())


class LossMapCurveSerialization(unittest.TestCase):
    def setUp(self):
        self.mixin = ProbabilisticEventMixin()
        self.mixin.params = {
            'NUMBER_OF_SEISMICITY_HISTORIES': 0,
            'NUMBER_OF_LOGIC_TREE_SAMPLES': 0,
            'INVESTIGATION_TIME': 0.0,
            'OUTPUT_DIR': 'foo',
        }
        self.mixin.serialize_results_to = ['db', 'xml']
        self.mixin.job_id = -1
        self.mixin.base_path = '/tmp'
        self.mixin.blocks_keys = []
        self.mixin.store_exposure_assets = lambda: None
        self.mixin.store_vulnerability_model = lambda: None
        self.mixin.partition = lambda: None

    def test_loss_map_serialized_if_conditional_loss_poes(self):
        self.mixin.params['CONDITIONAL_LOSS_POE'] = '0.01 0.02'

        with patch('openquake.risk.job.probabilistic'
                   '.aggregate_loss_curve.plot_aggregate_curve'):
            with patch('openquake.output.risk.create_loss_map_writer') as clw:
                clw.return_value = None

                self.mixin.execute()
                self.assertTrue(clw.called)

    def test_loss_map_not_serialized_unless_conditional_loss_poes(self):
        with patch('openquake.risk.job.probabilistic'
                   '.aggregate_loss_curve.plot_aggregate_curve'):
            with patch('openquake.output.risk.create_loss_map_writer') as clw:
                clw.return_value = None

                self.mixin.execute()
                self.assertFalse(clw.called)
