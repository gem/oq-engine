# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
import operator
import numpy

from openquake.baselib import datastore, hdf5, parallel, general
from openquake.baselib.python3compat import zip
from openquake.hazardlib.calc.filters import getdefault
from openquake.risklib import riskmodels
from openquake.risklib.scientific import LossesByAsset
from openquake.risklib.riskinput import (
    cache_epsilons, get_assets_by_taxo, get_output)
from openquake.calculators import base, event_based, getters
from openquake.calculators.scenario_risk import highest_losses
from openquake.calculators.post_risk import PostRiskCalculator

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
TWO32 = 2 ** 32
get_n_occ = operator.itemgetter(1)

gmf_info_dt = numpy.dtype([('ridx', U32), ('task_no', U16),
                           ('nsites', U16), ('gmfbytes', F32), ('dt', F32)])


def calc_risk(hazard, param, monitor):
    gmfs = numpy.concatenate(hazard['gmfs'])
    events = numpy.concatenate(hazard['events'])
    mon_risk = monitor('computing risk', measuremem=False)
    mon_agg = monitor('aggregating losses', measuremem=False)
    dstore = datastore.read(param['hdf5path'])
    with monitor('getting assets'):
        assetcol = dstore['assetcol']
        assets_by_site = assetcol.assets_by_site()
    with monitor('getting crmodel'):
        crmodel = riskmodels.CompositeRiskModel.read(dstore)
        weights = dstore['weights'][()]
    E = len(events)
    L = len(param['lba'].loss_names)
    shape = assetcol.tagcol.agg_shape((E, L), param['aggregate_by'])
    elt_dt = [('event_id', U32), ('rlzi', U16), ('loss', (F32, shape[1:]))]
    alt = general.AccumDict(accum=numpy.zeros(L, F32))  # aid, eid -> loss
    acc = dict(elt=numpy.zeros(shape, F32),  # shape (E, L, T...)
               gmf_info=[], events_per_sid=0, lossbytes=0)
    arr = acc['elt']
    lba = param['lba']
    tempname = param['tempname']
    tagnames = param['aggregate_by']
    eid2rlz = dict(events[['id', 'rlz_id']])
    eid2idx = {eid: idx for idx, eid in enumerate(eid2rlz)}
    n = param['highest_losses']
    minimum_loss = param['minimum_loss']
    for sid, haz in general.group_array(gmfs, 'sid').items():
        assets_on_sid = assets_by_site[sid]
        if len(assets_on_sid) == 0:
            continue
        acc['events_per_sid'] += len(haz)
        if param['avg_losses']:
            ws = weights[[eid2rlz[eid] for eid in haz['eid']]]
        assets_by_taxo = get_assets_by_taxo(assets_on_sid, tempname)
        eidx = [eid2idx[eid] for eid in haz['eid']]
        with mon_risk:
            out = get_output(crmodel, assets_by_taxo, haz)
        with mon_agg:
            for a, asset in enumerate(assets_on_sid):
                aid = asset['ordinal']
                tagi = asset[tagnames] if tagnames else ()
                tagidxs = tuple(idx - 1 for idx in tagi)
                losses_by_lt = {}
                for lti, lt in enumerate(crmodel.loss_types):
                    lratios = out[lt][a]
                    if lt == 'occupants':
                        losses = lratios * asset['occupants_None']
                    else:
                        losses = lratios * asset['value-' + lt]
                    losses_by_lt[lt] = losses
                    for loss, eid in highest_losses(losses, out.eids, n):
                        if loss > minimum_loss[lti]:
                            alt[aid, eid][lti] = loss
                for loss_idx, losses in lba.compute(asset, losses_by_lt):
                    arr[(eidx, loss_idx) + tagidxs] += losses
                    if param['avg_losses']:
                        lba.losses_by_A[aid, loss_idx] += (
                            losses @ ws * param['ses_ratio'])
                    acc['lossbytes'] += losses.nbytes
    if len(gmfs):
        acc['events_per_sid'] /= len(gmfs)
    acc['gmf_info'] = numpy.array(hazard['gmf_info'], gmf_info_dt)
    acc['elt'] = numpy.fromiter(  # this is ultra-fast
        ((event['id'], event['rlz_id'], losses)  # losses (L, T...)
         for event, losses in zip(events, arr) if losses.sum()), elt_dt)
    acc['alt'] = numpy.fromiter(  # already sorted by aid
        ((aid, eid, loss) for (aid, eid), loss in alt.items()),
        param['ael_dt'])
    if param['avg_losses']:
        acc['losses_by_A'] = param['lba'].losses_by_A
        # without resetting the cache the sequential avg_losses would be wrong!
        del param['lba'].__dict__['losses_by_A']
    return acc


def len_gmfs(hazard):
    return sum(len(gmfs) for gmfs in hazard['gmfs'])


def ebrisk(rupgetters, srcfilter, param, monitor):
    """
    :param rupgetters: RuptureGetters with 1 rupture each
    :param srcfilter: a SourceFilter
    :param param: dictionary of parameters coming from oqparam
    :param monitor: a Monitor instance
    :returns: a dictionary with keys elt, alt, ...
    """
    mon_haz = monitor('getting hazard', measuremem=False)
    mon_rup = monitor('getting ruptures', measuremem=False)
    hazard = dict(gmfs=[], events=[], gmf_info=[])
    for rupgetter in rupgetters:
        with mon_rup:
            gg = getters.GmfGetter(rupgetter, srcfilter, param['oqparam'])
            gg.init()
        if not gg.computers:  # filtered out rupture
            continue
        [c] = gg.computers
        with mon_haz:
            data = c.compute_all(gg.min_iml, gg.rlzs_by_gsim)
            hazard['gmfs'].append(data)
            hazard['events'].append(c.rupture.get_events(gg.rlzs_by_gsim))
        hazard['gmf_info'].append(
            (c.rupture.ridx, mon_haz.task_no, len(c.sids),
             data.nbytes, mon_haz.dt))
        if len_gmfs(hazard) > param['max_gmfs_size']:
            yield calc_risk, hazard, param
            hazard = dict(gmfs=[], events=[], gmf_info=[])
    if len_gmfs(hazard):
        yield calc_risk(hazard, param, monitor)


@base.calculators.add('ebrisk')
class EbriskCalculator(event_based.EventBasedCalculator):
    """
    Event based PSHA calculator generating event loss tables
    """
    core_task = ebrisk
    is_stochastic = True
    precalc = 'event_based'
    accept_precalc = ['event_based', 'event_based_risk', 'ucerf_hazard']

    def pre_execute(self):
        oq = self.oqparam
        oq.ground_motion_fields = False
        super().pre_execute()
        self.param['lba'] = lba = (
            LossesByAsset(self.assetcol, oq.loss_names,
                          self.policy_name, self.policy_dict))
        self.param['max_gmfs_size'] = oq.max_gmfs_size
        self.param['ses_ratio'] = oq.ses_ratio
        self.param['aggregate_by'] = oq.aggregate_by
        self.param['highest_losses'] = oq.highest_losses
        self.param['minimum_loss'] = [getdefault(oq.minimum_asset_loss, ln)
                                      for ln in oq.loss_names]
        self.param['ael_dt'] = ael_dt = self.crmodel.aid_eid_loss_dt(
            oq.loss_names)
        self.A = A = len(self.assetcol)
        self.datastore.create_dset('loss_data/data', ael_dt)
        self.datastore.create_dset('loss_data/indices', F32, (A, 2))
        self.param.pop('oqparam', None)  # unneeded
        self.L = L = len(lba.loss_names)
        A = len(self.assetcol)
        self.datastore.create_dset('avg_losses-stats', F32, (A, 1, L))  # mean
        shp = self.assetcol.tagcol.agg_shape((L,), oq.aggregate_by)
        elt_dt = [('event_id', U32), ('rlzi', U16), ('loss', (F32, shp))]
        elt_nbytes = 4 * self.E * numpy.prod(shp)
        logging.info('Approx size of the event loss table: %s',
                     general.humansize(elt_nbytes))
        if elt_nbytes / (oq.concurrent_tasks or 1) > TWO32:
            raise RuntimeError('The event loss table is too big to be transfer'
                               'red with %d tasks' % oq.concurrent_tasks)
        self.datastore.create_dset('losses_by_event', elt_dt)
        self.zerolosses = numpy.zeros(shp, F32)  # to get the multi-index
        self.datastore.create_dset('gmf_info', gmf_info_dt)

    def execute(self):
        self.datastore.flush()  # just to be sure
        oq = self.oqparam
        parent = self.datastore.parent
        if parent:
            grp_indices = parent['ruptures'].attrs['grp_indices']
            dstore = parent
            csm_info = parent['csm_info']
        else:
            grp_indices = self.datastore['ruptures'].attrs['grp_indices']
            dstore = self.datastore
            csm_info = self.csm_info
        self.set_param(
            hdf5path=self.datastore.filename,
            task_duration=oq.task_duration or 1200,  # 20min
            tempname=cache_epsilons(
                self.datastore, oq, self.assetcol, self.crmodel, self.E))

        self.init_logic_tree(csm_info)
        trt_by_grp = csm_info.grp_by("trt")
        samples = csm_info.get_samples_by_grp()
        rlzs_by_gsim_grp = csm_info.get_rlzs_by_gsim_grp()
        ngroups = 0
        fe = 0
        eslices = self.datastore['eslices']
        allargs = []
        srcfilter = self.src_filter(self.datastore.tempname)
        rups_per_block = min(numpy.ceil(  # at max 500 ruptures per block
            len(dstore['ruptures']) / (oq.concurrent_tasks or 1)), 500)
        for grp_id, rlzs_by_gsim in rlzs_by_gsim_grp.items():
            start, stop = grp_indices[grp_id]
            if start == stop:  # no ruptures for the given grp_id
                continue
            ngroups += 1
            rup_array = dstore['ruptures'][start:stop]
            rgetter = getters.RuptureGetter(
                rup_array, dstore.filename, grp_id,
                trt_by_grp[grp_id], samples[grp_id], rlzs_by_gsim,
                eslices[fe:fe + stop - start, 0])
            for rgetters in general.block_splitter(
                    rgetter.split(), rups_per_block):
                allargs.append((rgetters, srcfilter, self.param))
            fe += stop - start
        logging.info('Sending %d/%d source groups with ruptures',
                     ngroups, len(rlzs_by_gsim_grp))
        self.events_per_sid = []
        self.lossbytes = 0
        self.datastore.swmr_on()
        smap = parallel.Starmap(
            self.core_task.__func__, allargs, h5=self.datastore.hdf5)
        alt = numpy.concatenate(smap.reduce(self.agg_dicts, []))
        logging.info('Storing the asset loss table')
        with self.monitor('storing asset loss table'):
            alt.sort(order='aid')
            self.datastore['loss_data/data'] = alt
            indices = numpy.zeros((self.A, 2), U32)
            for aid, [startstop] in general.get_indices(alt['aid']).items():
                indices[aid] = startstop
            self.datastore['loss_data/indices'][:] = indices
        gmf_bytes = self.datastore['gmf_info']['gmfbytes'].sum()
        logging.info(
            'Produced %s of GMFs', general.humansize(gmf_bytes))
        logging.info(
            'Produced %s of losses', general.humansize(self.lossbytes))
        return 1

    def agg_dicts(self, alts, dic):
        """
        :param alts: list of asset loss tables
        :param dic: dictionary with keys elt, losses_by_A
        """
        if not dic or len(dic['elt']) == 0:
            return alts
        self.oqparam.ground_motion_fields = False  # hack
        elt = dic['elt']
        hdf5.extend(self.datastore['gmf_info'], dic['gmf_info'])
        with self.monitor('saving losses_by_event'):
            hdf5.extend(self.datastore['losses_by_event'], elt)
        if len(dic['alt']):
            alts.append(dic['alt'])
        if self.oqparam.avg_losses:
            with self.monitor('saving avg_losses'):
                self.datastore['avg_losses-stats'][:, 0] += dic['losses_by_A']
        self.events_per_sid.append(dic['events_per_sid'])
        self.lossbytes += dic['lossbytes']
        return alts

    def post_execute(self, dummy):
        """
        Compute and store average losses from the losses_by_event dataset,
        and then loss curves and maps.
        """
        oq = self.oqparam
        if oq.avg_losses:
            self.datastore['avg_losses-stats'].attrs['stats'] = [b'mean']
        prc = PostRiskCalculator(oq, self.datastore.calc_id)
        prc.datastore.parent = self.datastore.parent
        prc.run()
