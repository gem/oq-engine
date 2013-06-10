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


from nose.plugins.attrib import attr as noseattr

from qa_tests import risk

from openquake.engine.db import models


class EventBaseQATestCase1(risk.CompleteTestCase,
                           risk.LogicTreeBasedTestCase,
                           risk.End2EndRiskQATestCase):
    hazard_cfg = os.path.join(os.path.dirname(__file__), 'job_haz.ini')
    risk_cfg = os.path.join(os.path.dirname(__file__), 'job_risk.ini')

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
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'nonstructural', u'a3'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'nonstructural', u'a2'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'nonstructural', u'a1'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'nonstructural', u'a0'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'contents', u'a3'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'contents', u'a2'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'contents', u'a1'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'contents', u'a0'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'structural', u'a3'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'structural', u'a2'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'structural', u'a1'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
                None, None, False, False,
                u'structural', u'a0'
             ): self.DO_NOT_CHECK,
            (u'loss_curve', models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)),
                None, None, False, False,
                u'nonstructural', u'a3'
             ): self.DO_NOT_CHECK,
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
