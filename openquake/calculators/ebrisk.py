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

from openquake.baselib import hdf5, datastore
from openquake.baselib.general import group_array, humansize
from openquake.baselib.python3compat import zip, encode
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.hazardlib.calc.stochastic import TWO32
from openquake.risklib import riskinput, scientific
from openquake.calculators import base, event_based, getters
from openquake.calculators.export.loss_curves import get_loss_builder

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
U64 = numpy.uint64


def ebrisk(rupgetter, srcfilter, param, monitor):
    """
    :param rupgetter:
        a RuptureGetter instance
    :param srcfilter:
        a SourceFilter instance
    :param param:
        a dictionary of parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :returns:
        an ArrayWrapper with shape (E, L, T, ...)
    """
    riskmodel = param['riskmodel']
    L = len(riskmodel.lti)
    with monitor('getting ruptures'):
        ebruptures = rupgetter.get_ruptures(srcfilter)
    with monitor('getting assetcol'):
        with datastore.read(rupgetter.hdf5path) as dstore:
            assetcol = dstore['assetcol']
        assets_by_site = assetcol.assets_by_site()
    getter = getters.GmfGetter(
        rupgetter.rlzs_by_gsim, ebruptures, srcfilter.sitecol,
        param['oqparam'], param['min_iml'])
    tagnames = param['aggregate_by']
    with monitor('getting hazard'):
        getter.init()  # instantiate the computers
        data = numpy.fromiter(getter.gen_gmv(rlzidx=False), getter.gmv_dt)
        haz_by_sid = group_array(data, 'sid')
    eids = numpy.unique(data['eid'])
    eid2idx = {eid: idx for idx, eid in enumerate(eids)}
    shape = assetcol.agg_shape(len(eids), L, tagnames)
    acc = numpy.zeros(shape, F32)  # shape (E, L, T, ...)
    for loss_type, asset, eids_, loss_ratios in getter.gen_risk(
            assets_by_site, riskmodel, haz_by_sid):
        losses = asset.value(loss_type) * loss_ratios * param['ses_ratio']
        lti = riskmodel.lti[loss_type]
        tagi = assetcol.array[asset.ordinal][tagnames]
        tagidxs = tuple(idx - 1 for idx in tagi)
        for eid, loss in zip(eids_, losses):
            acc[(eid2idx[eid], lti) + tagidxs] += loss
    return hdf5.ArrayWrapper(acc, {'eids': eids})


@base.calculators.add('ebrisk')
class EbriskCalculator(event_based.EventBasedCalculator):
    """
    Event based PSHA calculator generating event loss tables
    """
    core_task = ebrisk
    is_stochastic = True

    def pre_execute(self):
        super().pre_execute()
        # save a copy of the assetcol in hdf5cache
        with hdf5.File(self.hdf5cache) as cache:
            cache['assetcol'] = self.assetcol
        self.param['aggregate_by'] = self.oqparam.aggregate_by
        # initialize the riskmodel
        self.riskmodel.taxonomy = self.assetcol.tagcol.taxonomy
        self.param['riskmodel'] = self.riskmodel
        self.param['ses_ratio'] = self.oqparam.ses_ratio

    def agg_dicts(self, dummy, arr):
        """
        :param dummy: unused parameter
        :param arr: ArrayWrapper with an attribute .eids
        """
        if 'aggloss' not in self.datastore:  # first time
            L = len(self.riskmodel.lti)
            shp = self.assetcol.agg_shape(len(self.eid2idx), L,
                                          self.oqparam.aggregate_by)
            logging.info('Creating aggloss of shape %s, %s', shp,
                         humansize(numpy.product(shp) * 4))
            self.datastore.create_dset('aggloss', F32, shp)
            self.oqparam.ground_motion_fields = False
        with self.monitor('saving aggloss', measuremem=True):
            if len(arr):
                idx = [self.eid2idx[eid] for eid in arr.eids]
                self.datastore['aggloss'][idx] = arr
        return 1

    def post_execute(self, dummy):
        """
        Compute and store average losses from the aggloss dataset,
        and then loss curves and maps.
        """
        pass
