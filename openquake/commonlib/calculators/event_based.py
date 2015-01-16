#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import random
import operator
import itertools
import collections

import numpy

from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc.filters import \
    filter_sites_by_distance_to_rupture
from openquake.hazardlib import site
from openquake.commonlib import readinput, parallel
from openquake.baselib.general import AccumDict

from openquake.commonlib.writers import save_csv
from openquake.commonlib.calculators import base, calc

SESRupture = collections.namedtuple(
    'SESRupture', 'rupture site_indices seed tag trt_model_id')


def compute_ruptures(sources, sitecol, monitor):
    """
    :param sources:
        List of commonlib.source.Source tuples
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param monitor:
        monitor instance
    :returns:
        a dictionary trt_model_id -> [Rupture instances]
    """
    trt_model_id = sources[0].trt_model_id
    oq = monitor.oqparam
    all_ses = range(1, oq.ses_per_logic_tree_path + 1)
    sesruptures = []

    # Compute and save stochastic event sets
    rnd = random.Random()
    for src in sources:
        rnd.seed(src.seed)  # keep this here and not after the filtering;
        # in this way changing the maximum distance does not change the
        # generated seeds, which could be surprising

        s_sites = src.filter_sites_by_distance_to_source(
            oq.maximum_distance, sitecol)
        if s_sites is None:
            continue

        # the dictionary `ses_num_occ` contains [(ses, num_occurrences)]
        # for each occurring rupture for each ses in the ses collection
        ses_num_occ = collections.defaultdict(list)
        # generating ruptures for the given source
        for rup_no, rup in enumerate(src.iter_ruptures(), 1):
            rup.rup_no = rup_no
            for ses_idx in all_ses:
                numpy.random.seed(rnd.randint(0, calc.MAX_INT))
                num_occurrences = rup.sample_number_of_occurrences()
                if num_occurrences:
                    ses_num_occ[rup].append((ses_idx, num_occurrences))

        # NB: the number of occurrences is very low, << 1, so it is
        # more efficient to filter only the ruptures that occur, i.e.
        # to call sample_number_of_occurrences() *before* the filtering
        for rup in sorted(ses_num_occ, key=operator.attrgetter('rup_no')):
            # filtering ruptures
            r_sites = filter_sites_by_distance_to_rupture(
                rup, oq.maximum_distance, s_sites)
            if r_sites is None:
                # ignore ruptures which are far away
                del ses_num_occ[rup]  # save memory
                continue
            indices = r_sites.indices if len(r_sites) < len(sitecol) \
                else None  # None means that nothing was filtered

            # creating SESRuptures
            for ses_idx, num_occurrences in ses_num_occ[rup]:
                for occ_no in range(1, num_occurrences + 1):
                    seed = rnd.randint(0, calc.MAX_INT)
                    tag = 'trt=%02d|ses=%04d|src=%s|rup=%03d-%02d' % (
                        trt_model_id, ses_idx, src.source_id, rup.rup_no,
                        occ_no)
                    sesruptures.append(
                        SESRupture(rup, indices, seed, tag, trt_model_id))

    return {trt_model_id: sesruptures}


@base.calculators.add('event_based_rupture')
class EventBasedRuptureCalculator(base.HazardCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    core_func = compute_ruptures

    def pre_execute(self):
        """
        Set a seed on each source
        """
        super(EventBasedRuptureCalculator, self).pre_execute()
        rnd = random.Random()
        rnd.seed(self.oqparam.random_seed)
        for src in self.composite_source_model.sources:
            src.seed = rnd.randint(0, calc.MAX_INT)

    def execute(self):
        """
        Run in parallel `core_func(sources, sitecol, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        monitor = self.monitor(self.core_func.__name__)
        monitor.oqparam = self.oqparam
        sources = list(self.composite_source_model.sources)
        return parallel.apply_reduce(
            self.core_func.__func__,
            (sources, self.sitecol, monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=operator.attrgetter('weight'),
            key=operator.attrgetter('trt_model_id'))

    def post_execute(self, result):
        for trt_id in sorted(result):
            for sr in result[trt_id]:
                for tag in sorted(sr.tags):
                    print tag
        return {}


def compute_gmfs_and_curves(ses_ruptures, sitecol, gsims_assoc, monitor):
    """
    :param ses_ruptures:
        a list of blocks of SESRuptures with homogeneous TrtModel
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param gsims_assoc:
        associations trt_model_id -> gsims
    :param monitor:
        a Monitor instance
    :returns:
        a dictionary trt_model_id -> curves_by_gsim
        where the list of bounding boxes is empty
    """
    oq = monitor.oqparam

    result = {}  # trt_model_id -> curves_by_gsim
    # NB: by construction each block is a non-empty list with
    # ruptures of the trt_model_id
    trt_id = ses_ruptures[0].trt_model_id
    gsims = sorted(gsims_assoc[trt_id])
    gcalc = calc.GmfCalculator(
        map(from_string, oq.imtls), gsims, trt_id,
        getattr(oq, 'truncation_level', None), readinput.get_correl_model(oq))

    for rupture, group in itertools.groupby(
            ses_ruptures, operator.attrgetter('rupture')):
        srs = list(group)
        indices = srs[0].site_indices
        r_sites = (sitecol if indices is None else
                   site.FilteredSiteCollection(indices, sitecol))
        for gsim_name, rows in gcalc.calc_gmfs(
                r_sites, rupture, [(sr.tag, sr.seed) for sr in srs]):
            if oq.ground_motion_fields:
                fname = os.path.join(
                    oq.export_dir, '%s-%s.csv' % (trt_id, gsim_name))
                save_csv(fname, rows, mode='a')

    if getattr(oq, 'hazard_curves_from_gmfs', None):
        for gsim, curves_by_imt in gcalc.to_haz_curves(
                sitecol.sids, oq.imtls,
                oq.investigation_time, oq.ses_per_logic_tree_path):
            result[trt_id, gsim] = {imt: curve for imt, curve in zip(
                gcalc.sorted_imts, curves_by_imt)}

    return result


@base.calculators.add('event_based')
class EventBasedCalculator(base.HazardCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    hazard_calculator = 'event_based_rupture'
    core_func = compute_gmfs_and_curves

    def pre_execute(self):
        haz_out = base.get_hazard(self)
        self.sitecol = haz_out['sitecol']
        self.rlzs_assoc = haz_out['rlzs_assoc']
        self.sesruptures = sorted(sum(haz_out['result'].itervalues(), []),
                                  key=operator.attrgetter('tag'))

        # touch output files
        for trt_id, gsim in self.rlzs_assoc:
            fname = os.path.join(
                self.oqparam.export_dir, '%s-%s.csv' % (trt_id, gsim))
            open(fname, 'w').close()

    def execute(self):
        """
        Run in parallel `core_func(sources, sitecol, monitor)`, by
        parallelizing on the ruptures according to their weight and
        tectonic region type.
        """
        monitor = self.monitor(self.core_func.__name__)
        monitor.oqparam = self.oqparam
        zero = AccumDict((key, AccumDict())
                         for key in self.rlzs_assoc)
        gsims_assoc = self.rlzs_assoc.get_gsims_by_trt_id()
        return parallel.apply_reduce(
            self.core_func.__func__,
            (self.sesruptures, self.sitecol, gsims_assoc, monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks, acc=zero,
            key=operator.attrgetter('trt_model_id'))

    post_execute = base.calculators['classical'].post_execute.__func__
