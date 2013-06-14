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

import numpy

from nose.plugins.attrib import attr as noseattr

from qa_tests import risk

from openquake.engine.db import models


class EventBaseQATestCase1(risk.CompleteTestCase, risk.FixtureBasedQATestCase):
    hazard_cfg = os.path.join(os.path.dirname(__file__), 'job_haz.ini')
    risk_cfg = os.path.join(os.path.dirname(__file__), 'job_risk.ini')

    hazard_calculation_fixture = "PEB QA test with 500 ses"

    @noseattr('qa', 'risk', 'event_based', 'e2e')
    def test(self):
        self._run_test()

    def expected_output_data(self):
        return {
            (u'loss_curve',
             models.Output.HazardMetadata(
                 investigation_time=50.0,
                 statistics=u'mean', quantile=None,
                 sm_path=None, gsim_path=None),
             u'mean', None, False, False, u'nonstructural', u'a3'
             ): self.DO_NOT_CHECK,
            (u'loss_curve',
             models.Output.HazardMetadata(
                 investigation_time=50.0,
                 statistics=u'mean', quantile=None,
                 sm_path=None, gsim_path=None),
             u'mean', None, False, False, u'nonstructural', u'a2'
             ): self.DO_NOT_CHECK,
            (u'loss_curve',
             models.Output.HazardMetadata(
                 investigation_time=50.0,
                 statistics=u'mean', quantile=None,
                 sm_path=None, gsim_path=None),
             u'mean', None, False, False, u'nonstructural', u'a1'
             ): self.DO_NOT_CHECK,
            (u'loss_curve',
             models.Output.HazardMetadata(
                 investigation_time=50.0,
                 statistics=u'mean', quantile=None,
                 sm_path=None, gsim_path=None),
             u'mean', None, False, False, u'nonstructural', u'a0'
             ): self.DO_NOT_CHECK,
            (u'loss_curve',
             models.Output.HazardMetadata(
                 investigation_time=50.0,
                 statistics=u'mean', quantile=None,
                 sm_path=None, gsim_path=None),
             u'mean', None, False, False, u'contents', u'a3'
             ): self.DO_NOT_CHECK,
            (u'loss_curve',
             models.Output.HazardMetadata(
                 investigation_time=50.0,
                 statistics=u'mean', quantile=None,
                 sm_path=None, gsim_path=None),
             u'mean', None, False, False, u'contents', u'a2'
             ): self.DO_NOT_CHECK,
            (u'loss_curve',
             models.Output.HazardMetadata(
                 investigation_time=50.0,
                 statistics=u'mean', quantile=None,
                 sm_path=None, gsim_path=None),
             u'mean', None, False, False, u'contents', u'a1'
             ): self.DO_NOT_CHECK,
            (u'loss_curve',
             models.Output.HazardMetadata(
                 investigation_time=50.0,
                 statistics=u'mean', quantile=None,
                 sm_path=None, gsim_path=None),
             u'mean', None, False, False, u'contents', u'a0'
             ): self.DO_NOT_CHECK,
            (u'loss_curve',
             models.Output.HazardMetadata(
                 investigation_time=50.0,
                 statistics=u'mean', quantile=None,
                 sm_path=None, gsim_path=None),
             u'mean', None, False, False, u'structural', u'a3'
             ): self.DO_NOT_CHECK,
            (u'loss_curve',
             models.Output.HazardMetadata(
                 investigation_time=50.0,
                 statistics=u'mean', quantile=None,
                 sm_path=None, gsim_path=None),
             u'mean', None, False, False, u'structural', u'a2'
             ): self.DO_NOT_CHECK,
            (u'loss_curve',
             models.Output.HazardMetadata(
                 investigation_time=50.0,
                 statistics=u'mean', quantile=None,
                 sm_path=None, gsim_path=None),
             u'mean', None, False, False, u'structural', u'a1'
             ): self.DO_NOT_CHECK,
            (u'loss_curve',
             models.Output.HazardMetadata(
                 investigation_time=50.0,
                 statistics=u'mean', quantile=None,
                 sm_path=None, gsim_path=None),
             u'mean', None, False, False, u'structural', u'a0'
             ): self.DO_NOT_CHECK,

###
### Checking loss curves corresponding to the hazard with branch = b1
###

###
### Non Structural loss type
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'nonstructural', u'a3'
             ): models.LossCurveData(
                 asset_value=2500,
                 loss_ratios=(numpy.array(
                     [0, 104.71, 209.43, 314.14, 418.86, 523.57, 628.29, 733,
                      837.71, 942.43, 1047.1, 1151.9, 1256.6, 1361.3, 1466,
                      1570.7, 1675.4, 1780.1, 1884.9, 1989.6]) / 2500),
                 poes=[0.23967, 0.23967, 0.23967, 0.18127, 0.10596, 0.073184,
                       0.044958, 0.033428, 0.02176, 0.017839, 0.015873,
                       0.005982, 0.005982, 0.001998, 0.001998, 0.001998,
                       0.001998, 0.001998, 0.001998, 0]),
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'nonstructural', u'a2'
             ): models.LossCurveData(
                 asset_value=500,
                 loss_ratios=(numpy.array(
                     [0, 5.2632, 10.526, 15.789, 21.053, 26.316, 31.579,
                      36.842, 42.105, 47.368, 52.632, 57.895, 63.158,
                      68.421, 73.684, 78.947, 84.211, 89.474, 94.737,
                      100]) / 500),
                 poes=[0.86547, 0.86547, 0.86547, 0.8283, 0.61326, 0.45773,
                       0.35725, 0.29531, 0.24573, 0.19265, 0.16306, 0.14101,
                       0.13064, 0.11662, 0.10596, 0.043046, 0.025665,
                       0.015873, 0.0099502, 0]),
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'nonstructural', u'a1'
             ): models.LossCurveData(
                 asset_value=1000,
                 loss_ratios=(numpy.array(
                     [0, 9.0553, 18.111, 27.166, 36.221, 45.276, 54.332,
                      63.387, 72.442, 81.498, 90.553, 99.608, 108.66,
                      117.72, 126.77, 135.83, 144.88, 153.94, 163,
                      172.05]) / 1000),
                 poes=[0.92018, 0.92018, 0.92018, 0.92018, 0.92018, 0.40548,
                       0.1597, 0.069469, 0.037287, 0.029554, 0.027612,
                       0.027612, 0.023714, 0.015873, 0.013902, 0.0099502,
                       0.005982, 0.001998, 0.001998, 0]),
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'nonstructural', u'a0'
             ): models.LossCurveData(
                 asset_value=1500,
                 loss_ratios=(numpy.array(
                     [0, 51.852, 103.7, 155.56, 207.41, 259.26, 311.11, 362.96,
                      414.82, 466.67, 518.52, 570.37, 622.22, 674.08, 725.93,
                      777.78, 829.63, 881.48, 933.33, 985.19]) / 1500),
                 poes=[0.14786, 0.14786, 0.14786, 0.13238, 0.091536, 0.048771,
                       0.033428, 0.025665, 0.011928, 0.011928, 0.0099502,
                       0.0099502, 0.0099502, 0.005982, 0.003992, 0.003992,
                       0.003992, 0.001998, 0.001998, 0]),

###
### Contents loss type
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'contents', u'a3'
             ): models.LossCurveData(
                 asset_value=1250,
                 loss_ratios=(numpy.array(
                     [0, 32.895, 65.789, 98.684, 131.58, 164.47, 197.37,
                      230.26, 263.16, 296.05, 328.95, 361.84, 394.74,
                      427.63, 460.53, 493.42, 526.32, 559.21, 592.11,
                      625]) / 1250),
                 poes=[0.98157, 0.98157, 0.91072, 0.23356, 0.091536, 0.050671,
                       0.02176, 0.019801, 0.011928, 0.0099502, 0.0099502,
                       0.005982, 0.003992, 0.003992, 0.003992, 0.003992,
                       0.001998, 0.001998, 0.001998, 0]	),
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'contents', u'a2'
             ): models.LossCurveData(
                 asset_value=250,
                 loss_ratios=(numpy.array(
                     [0, 13.158, 26.316, 39.474, 52.632, 65.789, 78.947,
                      92.105, 105.26, 118.42, 131.58, 144.74, 157.89,
                      171.05, 184.21, 197.37, 210.53, 223.68, 236.84,
                      250]) / 250),
                 poes=[0.86547, 0.86547, 0.75192, 0.46634, 0.39226, 0.3175,
                       0.26948, 0.23509, 0.19265, 0.16473, 0.14444, 0.13411,
                       0.13064, 0.1219, 0.11485, 0.10237, 0.031493, 0.019801,
                       0.011928, 0]),
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'contents', u'a1'
             ): models.LossCurveData(
                 asset_value=500,
                 loss_ratios=(numpy.array(
                     [0, 14.737, 29.474, 44.211, 58.947, 73.684, 88.421,
                      103.16, 117.89, 132.63, 147.37, 162.11, 176.84, 191.58,
                      206.32, 221.05, 235.79, 250.53, 265.26, 280]) / 500),
                 poes=[0.79154, 0.79154, 0.38982, 0.20228, 0.1289, 0.091536,
                       0.082406, 0.060117, 0.04113, 0.03536, 0.031493,
                       0.023714, 0.02176, 0.019801, 0.017839, 0.011928,
                       0.011928, 0.0099502, 0.0099502, 0]),
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'contents', u'a0'
             ): models.LossCurveData(
                 asset_value=750,
                 loss_ratios=(numpy.array(
                     [0, 9.5726, 19.145, 28.718, 38.29, 47.863, 57.436, 67.008,
                      76.581, 86.154, 95.726, 105.3, 114.87, 124.44, 134.02,
                      143.59, 153.16, 162.73, 172.31, 181.88]) / 750),
                 poes=[0.97122, 0.97122, 0.97122, 0.97122, 0.92935, 0.33635,
                       0.15465, 0.073184, 0.046866, 0.027612, 0.015873,
                       0.013902, 0.0079681, 0.005982, 0.005982, 0.005982,
                       0.005982, 0.005982, 0.003992, 0]),
###
### Structural loss type
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'structural', u'a3'
             ): models.LossCurveData(
                 asset_value=5000,
                 loss_ratios=(numpy.array(
                     [0, 210.53, 421.05, 631.58, 842.11, 1052.6, 1263.2,
                      1473.7, 1684.2, 1894.7, 2105.3, 2315.8, 2526.3,
                      2736.8, 2947.4, 3157.9, 3368.4, 3578.9, 3789.5,
                      4000]) / 5000),
                 poes=[0.98157, 0.98157, 0.18942, 0.080569, 0.048771, 0.02176,
                       0.017839, 0.011928, 0.0099502, 0.005982, 0.003992,
                       0.003992, 0.003992, 0.003992, 0.003992, 0.003992,
                       0.001998, 0.001998, 0.001998, 0]),
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'structural', u'a2'
             ): models.LossCurveData(
                 asset_value=1000,
                 loss_ratios=(numpy.array(
                     [0, 52.632, 105.26, 157.89, 210.53, 263.16, 315.79,
                      368.42, 421.05, 473.68, 526.32, 578.95, 631.58,
                      684.21, 736.84, 789.47, 842.11, 894.74, 947.37,
                      1000]) / 1000),
                 poes=[0.96768, 0.96768, 0.81768, 0.59908, 0.44234,
                       0.34949, 0.32159, 0.29672, 0.27675, 0.2427, 0.19587,
                       0.13064, 0.080569, 0.063869, 0.052568, 0.033428,
                       0.02176, 0.015873, 0.015873, 0]),
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'structural', u'a1'
             ): models.LossCurveData(
                 asset_value=2000,
                 loss_ratios=(numpy.array(
                     [0, 58.947, 117.89, 176.84, 235.79, 294.74, 353.68,
                      412.63, 471.58, 530.53, 589.47, 648.42, 707.37,
                      766.32, 825.26, 884.21, 943.16, 1002.1, 1061.1,
                      1120]) / 2000),
                 poes=[0.3134, 0.3134, 0.091536, 0.044958, 0.037287,
                       0.023714, 0.023714, 0.02176, 0.02176, 0.02176,
                       0.019801, 0.019801, 0.017839, 0.015873, 0.015873,
                       0.015873, 0.015873, 0.015873, 0.015873, 0]),
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'structural', u'a0'
             ): models.LossCurveData(
                 asset_value=3000,
                 loss_ratios=(numpy.array(
                     [0, 51.054, 102.11, 153.16, 204.22, 255.27, 306.32,
                      357.38, 408.43, 459.49, 510.54, 561.59, 612.65,
                      663.7, 714.76, 765.81, 816.86, 867.92, 918.97,
                      970.02]) / 3000),
                 poes=[0.97122, 0.97122, 0.97122, 0.92935, 0.24119, 0.091536,
                       0.046866, 0.03536, 0.02176, 0.015873, 0.013902,
                       0.0099502, 0.0079681, 0.005982, 0.005982, 0.005982,
                       0.005982, 0.005982, 0.003992, 0]),

###
### Checking loss curves corresponding to the hazard with branch = b2
###

###
### Non Structural loss type
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, False, False,
                u'nonstructural', u'a3'
             ): models.LossCurveData(
                 asset_value=2500,
                 loss_ratios=(numpy.array(
                     [0, 118.42, 236.84, 355.26, 473.68, 592.11, 710.53,
                      828.95, 947.37, 1065.8, 1184.2, 1302.6, 1421.1,
                      1539.5, 1657.9, 1776.3, 1894.7, 2013.2, 2131.6,
                      2250]) / 2500),
                 poes=[0.2212, 0.2212, 0.2212, 0.14101, 0.095163, 0.058235,
                       0.037287, 0.025665, 0.02176, 0.017839, 0.013902,
                       0.013902, 0.0099502, 0.0099502, 0.0099502, 0.005982,
                       0.003992, 0.003992, 0.003992, 0]),
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, False, False,
                u'nonstructural', u'a2'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, False, False,
                u'nonstructural', u'a1'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, False, False,
                u'nonstructural', u'a0'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, False, False,
                u'contents', u'a3'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, False, False,
                u'contents', u'a2'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, False, False,
                u'contents', u'a1'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, False, False,
                u'contents', u'a0'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, False, False,
                u'structural', u'a3'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, False, False,
                u'structural', u'a2'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, False, False,
                u'structural', u'a1'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, False, False,
                u'structural', u'a0'
             ): self.DO_NOT_CHECK,
            (u'agg_loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, True, False,
                u'nonstructural'
             ): self.DO_NOT_CHECK,
            (u'agg_loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, True, False,
                u'structural'
             ): self.DO_NOT_CHECK,
            (u'agg_loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, True, False,
                u'contents'
             ): self.DO_NOT_CHECK,
            (u'agg_loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, True, False,
                u'nonstructural'
             ): self.DO_NOT_CHECK,
            (u'agg_loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, True, False,
                u'structural'
             ): self.DO_NOT_CHECK,
            (u'agg_loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, True, False,
                u'contents'
             ): self.DO_NOT_CHECK,
        }

    def should_skip(self, output):
        return (output.output_type == "event_loss")
