# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
import collections
import logging
import numpy

from openquake.risklib import riskinput
from openquake.hazardlib import InvalidFile
from openquake.calculators import base, event_based, event_based_risk as ebr

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
U64 = numpy.uint64
F64 = numpy.float64  # higher precision to avoid task order dependency
stat_dt = numpy.dtype([('mean', F32), ('stddev', F32)])


@base.calculators.add('gmf_ebrisk')
class GmfEbRiskCalculator(base.RiskCalculator):
    """
    Run an event based risk calculation starting from precomputed GMFs
    """
    core_task = ebr.event_based_risk
    pre_calculator = None
    is_stochastic = True

    def pre_execute(self):
        logging.warn('%s is still experimental', self.__class__.__name__)
        base.RiskCalculator.pre_execute(self)
        oq = self.oqparam
        self.L = len(self.riskmodel.lti)
        self.T = len(self.assetcol.tags())
        self.A = len(self.assetcol)
        self.I = oq.insured_losses + 1
        if oq.hazard_calculation_id:  # read the GMFs from a previous calc
            assert 'gmfs' not in oq.inputs, 'no gmfs_file when using --hc!'
            parent = self.read_previous(oq.hazard_calculation_id)
            oqp = parent['oqparam']
            if oqp.ses_per_logic_tree_path != 1:
                logging.warn(
                    'The parent calculation was using ses_per_logic_tree_path'
                    '=%d != 1', oqp.ses_per_logic_tree_path)
            if oqp.investigation_time != oq.investigation_time:
                raise ValueError(
                    'The parent calculation was using investigation_time=%s'
                    ' != %s' % (oqp.investigation_time, oq.investigation_time))
            if oqp.minimum_intensity != oq.minimum_intensity:
                raise ValueError(
                    'The parent calculation was using minimum_intensity=%s'
                    ' != %s' % (oqp.minimum_intensity, oq.minimum_intensity))
            self.eids = parent['events']['eid']
            self.datastore['csm_info'] = parent['csm_info']
            self.rlzs_assoc = parent['csm_info'].get_rlzs_assoc()
            self.R = len(self.rlzs_assoc.realizations)
        else:  # read the GMFs from a file
            if 'site_model' in oq.inputs:
                raise InvalidFile('it makes no sense to define a site model in'
                                  ' %(job_ini)s' % oq.inputs)
            with self.monitor('reading GMFs', measuremem=True):
                fname = oq.inputs['gmfs']
                sids = self.sitecol.complete.sids
                if fname.endswith('.xml'):  # old approach
                    self.eids, self.R = base.get_gmfs(self)
                else:  # import csv
                    self.eids, self.R, self.gmdata = base.import_gmfs(
                        self.datastore, fname, sids)
                    event_based.save_gmdata(self, self.R)
        self.E = len(self.eids)
        eps = riskinput.make_epsilon_getter(
            len(self.assetcol), self.E, oq.asset_correlation,
            oq.master_seed, oq.ignore_covs or not self.riskmodel.covs)()
        self.riskinputs = self.build_riskinputs('gmf', eps, self.eids)
        self.param['gmf_ebrisk'] = True
        self.param['insured_losses'] = oq.insured_losses
        self.param['avg_losses'] = oq.avg_losses
        self.param['ses_ratio'] = oq.ses_ratio
        self.param['asset_loss_table'] = oq.asset_loss_table
        self.param['elt_dt'] = numpy.dtype(
            [('eid', U64), ('rlzi', U16), ('loss', (F32, (self.L * self.I,)))])
        self.taskno = 0
        self.start = 0
        avg_losses = self.oqparam.avg_losses
        if avg_losses:
            self.dset = self.datastore.create_dset(
                'avg_losses-rlzs', F32, (self.A, self.R, self.L * self.I))
        self.agglosses = numpy.zeros((self.E, self.R, self.L * self.I), F32)
        self.vals = self.assetcol.values()
        self.num_losses = numpy.zeros((self.A, self.R), U32)
        if oq.asset_loss_table:
            # save all_loss_ratios
            self.alr_nbytes = 0
            self.indices = collections.defaultdict(list)  # sid -> pairs

    def post_execute(self, result):
        """
        Save the event loss table
        """
        logging.info('Saving event loss table')
        with self.monitor('saving event loss table', measuremem=True):
            # saving also zeros is a lot faster than adding an `if loss.sum()`
            agglosses = numpy.fromiter(
                ((e, r, loss)
                 for e, losses in zip(self.eids, self.agglosses)
                 for r, loss in enumerate(losses) if loss.sum()),
                self.param['elt_dt'])
            self.datastore['agg_loss_table'] = agglosses
        ebr.EbriskCalculator.__dict__['postproc'](self)

    def combine(self, dummy, res):
        """
        :param dummy: unused parameter
        :param res: a result dictionary
        """
        ebr.EbriskCalculator.__dict__['save_losses'](self, res, offset=0)
        return 1
