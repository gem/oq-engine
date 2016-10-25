# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016 GEM Foundation
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
import numpy

from openquake.baselib.general import AccumDict
from openquake.risklib import riskinput
from openquake.commonlib import parallel, calc
from openquake.calculators import base
from openquake.calculators.ucerf_event_based import (
    UCERFEventBasedCalculator, DEFAULT_TRT)
from openquake.calculators.event_based_risk import (
    EbriskCalculator, losses_by_taxonomy)


def compute_ruptures(sources, sitecol, gsims, monitor):
    """
    :param sources: a sequence of UCERF sources
    :param sitecol: a SiteCollection instance
    :param gsims: a list of GSIMs
    :param monitor: a Monitor instance
    :returns: an AccumDict grp_id -> EBRuptures
    """
    [src] = sources  # there is a single source per UCERF branch
    integration_distance = monitor.maximum_distance[DEFAULT_TRT]
    res = AccumDict()
    res.calc_times = AccumDict()
    serial = 1
    event_mon = monitor('sampling ruptures', measuremem=False)
    res.num_events = 0
    res.trt = DEFAULT_TRT
    t0 = time.time()
    # set the seed before calling generate_event_set
    numpy.random.seed(monitor.seed + src.src_group_id)
    ebruptures = []
    eid = 0
    src.build_idx_set()
    background_sids = src.get_background_sids(sitecol, integration_distance)
    for ses_idx in range(1, monitor.ses_per_logic_tree_path + 1):
        with event_mon:
            rups, n_occs = src.generate_event_set(background_sids)
        for rup, n_occ in zip(rups, n_occs):
            rup.seed = monitor.seed  # to think
            rrup = rup.surface.get_min_distance(sitecol.mesh)
            r_sites = sitecol.filter(rrup <= integration_distance)
            if r_sites is None:
                continue
            indices = r_sites.indices
            events = []
            for occ in range(n_occ):
                events.append((eid, ses_idx, occ, 0))  # 0 is the sampling
                eid += 1
            if events:
                ebruptures.append(
                    calc.EBRupture(
                        rup, indices,
                        numpy.array(events, calc.event_dt),
                        src.source_id, src.src_group_id, serial))
                serial += 1
                res.num_events += len(events)
        res[src.src_group_id] = ebruptures
        res.calc_times[src.src_group_id] = (
            src.source_id, len(sitecol), time.time() - t0)
    return res


class List(list):
    """Trivial container returned by compute_losses"""


def compute_losses(ssm, sitecol, assetcol, riskmodel,
                   imts, trunc_level, correl_model, min_iml, monitor):
    """
    Compute the losses for a single source model.

    :param ssm: CompositeSourceModel containing a single source model
    :param sitecol: a SiteCollection instance
    :param assetcol: an AssetCollection instance
    :param riskmodel: a RiskModel instance
    :param imts: a list of Intensity Measure Types
    :param trunc_level: truncation level
    :param correl_model: correlation model
    :param min_iml: vector of minimum intensities, one per IMT
    :param monitor: a Monitor instance
    :returns: a List containing the losses by taxonomy and some attributes
    """
    [grp] = ssm.src_groups
    res = List()
    res.ruptures_by_grp = compute_ruptures(grp, sitecol, None, monitor)
    [(grp_id, ruptures)] = res.ruptures_by_grp.items()
    rlzs_assoc = ssm.info.get_rlzs_assoc()
    num_rlzs = len(rlzs_assoc.realizations)
    ri = riskinput.RiskInputFromRuptures(
        DEFAULT_TRT, rlzs_assoc, imts, sitecol, ruptures, trunc_level,
        correl_model, min_iml)
    res.append(losses_by_taxonomy(ri, riskmodel, assetcol, monitor))
    res.sm_id = ssm.sm_id
    res.num_events = len(ri.eids)
    start = res.sm_id * num_rlzs
    res.rlz_slice = slice(start, start + num_rlzs)
    return res


@base.calculators.add('ucerf_risk')
class UCERFRiskCalculator(EbriskCalculator):
    """
    Event based risk calculator for UCERF, parallelizing on the source models
    """
    pre_execute = UCERFEventBasedCalculator.__dict__['pre_execute']
    compute_ruptures = staticmethod(compute_ruptures)


@base.calculators.add('ucerf_risk_fast')
class UCERFRiskFastCalculator(EbriskCalculator):
    """
    Event based risk calculator for UCERF, parallelizing on the source models
    """
    pre_execute = UCERFEventBasedCalculator.__dict__['pre_execute']

    def execute(self):
        num_rlzs = len(self.rlzs_assoc.realizations)
        allres = parallel.starmap(compute_losses, self.gen_args()).submit_all()
        num_events = self.save_results(allres, num_rlzs)
        self.save_data_transfer(allres)
        return num_events
