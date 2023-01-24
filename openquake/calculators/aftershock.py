# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
Aftershock calculator
"""
import logging
import operator
import numpy
import pandas
from openquake.baselib import parallel, general
from openquake.calculators import base, preclassical

U32 = numpy.uint32
F32 = numpy.float32


# NB: this is called after a preclassical calculation
def build_rates(srcs):
    """
    :param srcs: a list of split sources of the same source group
    """
    out = {'src_id': [], 'rup_id': [], 'delta': []}
    for src in srcs:
        for i, rup in enumerate(src.iter_ruptures()):
            out['src_id'].append(src.id)
            out['rup_id'].append(src.offset + i)
            # TODO: add the aftershock logic to compute the deltas
            # right now using a fake delta = 10% of the occurrence_rate
            try:
                delta = rup.occurrence_rate * .1
            except AttributeError:  # nonpoissonian rupture
                delta = numpy.nan
            out['delta'].append(delta)
    out['src_id'] = U32(out['src_id'])
    out['rup_id'] = U32(out['rup_id'])
    out['delta'] = F32(out['delta'])
    return pandas.DataFrame(out)


@base.calculators.add('aftershock')
class AftershockCalculator(preclassical.PreClassicalCalculator):
    """
    Aftershock calculator storing a dataset `delta_rates`
    """
    def post_execute(self, csm):
        logging.warning('Aftershock calculations are still experimental')
        self.datastore['_csm'] = csm
        sources = csm.get_sources()
        dfs = list(parallel.Starmap.apply(
            build_rates, (sources,),
            weight=operator.attrgetter('num_ruptures'),
            key=operator.attrgetter('grp_id'),
            h5=self.datastore,
            concurrent_tasks=self.oqparam.concurrent_tasks))
        logging.info('Sorting rates')
        df = pandas.concat(dfs).sort_values(['src_id', 'rup_id'])
        size = 0
        all_deltas = []
        num_ruptures = self.datastore['source_info']['num_ruptures']
        logging.info('Grouping deltas by %d src_id', len(num_ruptures))
        for src_id, grp in df.groupby('src_id'):
            # sanity check on the number of ruptures per source
            assert len(grp) == num_ruptures[src_id], (
                len(grp), num_ruptures[src_id])
            all_deltas.append(grp.delta.to_numpy())
            size += len(grp) * 4
        logging.info('Storing {} inside {}::/delta_rates'.format(
            general.humansize(size), self.datastore.filename))
        self.datastore.hdf5.save_vlen('delta_rates', all_deltas)
