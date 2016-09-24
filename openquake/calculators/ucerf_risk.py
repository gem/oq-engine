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
from openquake.calculators import base, event_based
from openquake.calculators.ucerf_event_based import (
    UCERFEventBasedCalculator, DEFAULT_TRT)
from openquake.calculators.event_based_risk import EbriskCalculator


@base.calculators.add('ucerf_risk')
class UCERFRiskCalculator(EbriskCalculator):
    """
    Event based risk calculator for UCERF, parallelizing on the source models
    """
    pre_execute = UCERFEventBasedCalculator.__dict__['pre_execute']

    def compute_ruptures(self, src_group, sitecol, gsims, monitor):
        [ucerf] = src_group
        integration_distance = monitor.maximum_distance[DEFAULT_TRT]
        res = AccumDict()
        res.calc_times = AccumDict()
        serial = 1
        filter_mon = monitor('update_background_site_filter', measuremem=False)
        event_mon = monitor('sampling ruptures', measuremem=False)
        res.num_events = 0
        res.trt = DEFAULT_TRT

        t0 = time.time()
        with filter_mon:
            ucerf.update_background_site_filter(
                ucerf.branch_id, sitecol, integration_distance)

        # set the seed before calling generate_event_set
        numpy.random.seed(monitor.seed + src_group.id)
        ses_ruptures = []
        eid = 0
        for ses_idx in range(1, monitor.ses_per_logic_tree_path + 1):
            with event_mon:
                rups, n_occs = ucerf.generate_event_set(
                    src_group.branch_id, sitecol, integration_distance)
            for i, rup in enumerate(rups):
                rup.seed = monitor.seed  # to think
                rrup = rup.surface.get_min_distance(sitecol.mesh)
                r_sites = sitecol.filter(rrup <= integration_distance)
                if r_sites is None:
                    continue
                indices = r_sites.indices
                events = []
                for j in range(n_occs[i]):
                    events.append((eid, ses_idx, j, 0))  # 0 is the sampling ID
                    eid += 1
                if events:
                    ses_ruptures.append(
                        event_based.EBRupture(
                            rup, indices,
                            numpy.array(events, event_based.event_dt),
                            ucerf.source_id, src_group.id, serial))
                    serial += 1
                    res.num_events += len(events)
            res[src_group.id] = ses_ruptures
            res.calc_times[src_group.id] = (
                src_group.name, len(sitecol), time.time() - t0)
        return res
