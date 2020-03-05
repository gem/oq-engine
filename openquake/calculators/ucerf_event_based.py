# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2020 GEM Foundation
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
import time
import logging
import collections
import numpy

from openquake.baselib.general import AccumDict
from openquake.baselib.python3compat import zip
from openquake.hazardlib.calc import stochastic
from openquake.hazardlib.source.rupture import EBRupture
from openquake.calculators import base, event_based
from openquake.calculators.ucerf_base import DEFAULT_TRT

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64


def build_ruptures(sources, src_filter, param, monitor):
    """
    :param sources: a list with a single UCERF source
    :param param: extra parameters
    :param monitor: a Monitor instance
    :returns: an AccumDict grp_id -> EBRuptures
    """
    [src] = sources
    res = AccumDict()
    res.calc_times = []
    sampl_mon = monitor('sampling ruptures', measuremem=True)
    res.trt = DEFAULT_TRT
    src.src_filter = src_filter
    background_sids = src.get_background_sids()
    samples = getattr(src, 'samples', 1)
    n_occ = AccumDict(accum=0)
    t0 = time.time()
    eff_num_ses = param['ses_per_logic_tree_path'] * samples
    with sampl_mon:
        rups, occs = src.generate_event_set(background_sids, eff_num_ses)
        for rup, occ in zip(rups, occs):
            n_occ[rup] += occ
    tot_occ = sum(n_occ.values())
    dic = {'eff_ruptures': {DEFAULT_TRT: src.num_ruptures}}
    eb_ruptures = [EBRupture(rup, src.id, src.src_group_id, n, samples)
                   for rup, n in n_occ.items()]
    dic['rup_array'] = stochastic.get_rup_array(eb_ruptures, src_filter)
    dt = time.time() - t0
    n = len(src_filter.sitecol)
    dic['calc_times'] = {src.id: numpy.array([tot_occ, n, dt], F32)}
    return dic


# NB: the old name ucerf_hazard is kept for backward compatibility
@base.calculators.add('ucerf_event_based', 'ucerf_hazard')
class UCERFHazardCalculator(event_based.EventBasedCalculator):
    """
    Event based PSHA calculator generating the ruptures and GMFs together
    """
    build_ruptures = build_ruptures
    accept_precalc = ['ucerf_event_based']

    def pre_execute(self):
        """
        parse the logic tree and source model input
        """
        logging.warning('%s is still experimental', self.__class__.__name__)
        self.read_inputs()  # read the site collection
        logging.info('Found %d source model logic tree branches',
                     len(self.csm.sm_rlzs))
        self.datastore['sitecol'] = self.sitecol
        self.eid = collections.Counter()  # sm_id -> event_id
        self.sm_by_grp = self.csm.info.get_sm_by_grp()
        self.init_logic_tree(self.csm.info)
        if not self.oqparam.imtls:
            raise ValueError('Missing intensity_measure_types!')
        self.precomputed_gmfs = False
