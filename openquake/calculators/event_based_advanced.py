# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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

import logging
import numpy

from openquake.calculators import base
from openquake.baselib import parallel
from openquake.baselib.general import AccumDict
from openquake.baselib.general import WeightedSequence
from openquake.calculators.event_based import EventBasedCalculator
from openquake.calculators.event_based import by_grp, store_rlzs_by_grp

F32 = numpy.float32


@base.calculators.add('event_based_advanced')
class EventBasedAdvancedCalculator(EventBasedCalculator):
    """
    This is an extension of the Event Based calculator created to deal with
    groups of sources either modelled as a cluster and/or containing mutually
    exclusive sources or ruptures.
    """

    def from_sources(self, par):
        """
        Prefilter the composite source model and store the source_info
        """
        oq = self.oqparam
        gsims_by_trt = self.csm.gsim_lt.values

        def weight_src(src):
            return src.num_ruptures

        logging.info('Building ruptures')
        smap = parallel.Starmap(
            self.build_ruptures.__func__, monitor=self.monitor())
        eff_ruptures = AccumDict(accum=0)  # grp_id => potential ruptures
        calc_times = AccumDict(accum=numpy.zeros(3, F32))
        ses_idx = 0
        for sm_id, sm in enumerate(self.csm.source_models):
            logging.info('Sending %s', sm)
            for sg in sm.src_groups:
                if not sg.sources:
                    continue
                par['gsims'] = gsims_by_trt[sg.trt]
                # Check cases where we do not want to split the group into
                # pieces
                par['group'] = False
                par['tom'] = None
                if sg.temporal_occurrence_model and (
                        sg.src_interdep in 'mutex' or
                        sg.rup_interdep in 'mutex' or
                        sg.cluster):
                    par['tom'] = sg.temporal_occurrence_model
                    par['group'] = True
                    par['cluster'] = sg.cluster
                    par['src_interdep'] = sg.src_interdep
                    par['rup_interdep'] = sg.rup_interdep
                    # Here we create a WeightedSequence similarly to what is
                    # done with traditional sources
                    dat = [(s, 1.) for s in sg.sources]
                    block = WeightedSequence(dat)
                    smap.submit(block, par)

                # This is the processing for traditional sources
                else:
                    for block in self.block_splitter(
                            sg.sources, weight_src, by_grp):
                        # TODO: The block has a number of attributes
                        # originally assigned to the group. It's unclear (to
                        # me) why these properties are transferred to the
                        # source
                        if 'ucerf' in oq.calculation_mode:
                            for i in range(oq.ses_per_logic_tree_path):
                                par['ses_seeds'] = [(ses_idx,
                                                     oq.ses_seed + i + 1)]
                                smap.submit(block, par)
                                ses_idx += 1
                        else:
                            smap.submit(block, par)

        mon = self.monitor('saving ruptures')
        for dic in smap:
            if dic['calc_times']:
                calc_times += dic['calc_times']
            if dic['eff_ruptures']:
                eff_ruptures += dic['eff_ruptures']
            if dic['rup_array']:
                with mon:
                    self.rupser.save(dic['rup_array'])
        self.rupser.close()

        # logic tree reduction, must be called before storing the events
        self.store_csm_info(eff_ruptures)
        store_rlzs_by_grp(self.datastore)
        self.init_logic_tree(self.csm.info)
        with self.monitor('store source_info', autoflush=True):
            self.store_source_info(calc_times)

        logging.info('Reordering the ruptures and storing the events')
        attrs = self.datastore.getitem('ruptures').attrs
        sorted_ruptures = self.datastore.getitem('ruptures').value
        # order the ruptures by serial
        sorted_ruptures.sort(order='serial')
        self.datastore['ruptures'] = sorted_ruptures
        self.datastore.set_attrs('ruptures', **attrs)
        rgetters = self.save_events(sorted_ruptures)
        return ((rgetter, self.src_filter, par) for rgetter in rgetters)
