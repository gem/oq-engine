# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2026 GEM Foundation
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

import os.path
import logging
import operator
from contextlib import nullcontext
from functools import partial
import numpy
import pandas
from scipy import sparse

from openquake.baselib import hdf5, performance, general, config
from openquake.hazardlib import stats, InvalidFile
from openquake.risklib import riskmodels
from openquake.commonlib.calc import starmap_from_gmfs
from openquake.risklib.scientific import (
    total_losses, insurance_losses, MultiEventRNG, LOSSID, LOSSTYPE)
from openquake.calculators import base, event_based, views
from openquake.calculators.post_risk import (
    PostRiskCalculator, post_aggregate, fix_dtypes, fix_investigation_time)

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64
TWO16 = 2 ** 16
TWO24 = 2 ** 24
TWO32 = U64(2 ** 32)
# AE_MAX chosen so that China runs with 3 GB per core
AE_MAX = 1.2E8
get_n_occ = operator.itemgetter(1)


@views.view.add('calc_risk')
def view_calc_risk(token, dstore):
    """
    Compute the risk_by_event table starting from GMFs
    """
    _, event_id = token.split(':')
    oq = dstore['oqparam']
    assetcol = dstore['assetcol']
    set_oqparam(oq, assetcol, dstore)
    crmodel = riskmodels.CompositeRiskModel.read(dstore, oq)
    gmf_df = dstore.read_df('gmf_data')
    gmf_df = gmf_df[gmf_df.eid == int(event_id)]
    ws = dstore['weights']
    rlz_id = dstore['events']['rlz_id']
    aggids, _ = assetcol.build_aggids(oq.aggregate_by)
    agg_keys = numpy.concatenate(
        [dstore['agg_keys'][:], numpy.array([b'total'])])
    ARK = (oq.A, len(ws), oq.K)
    if oq.ignore_master_seed or oq.ignore_covs:
        rng = None
    else:
        rng = MultiEventRNG(oq.master_seed, gmf_df.eid.unique(),
                            int(oq.asset_correlation))

    mon = performance.Monitor()
    outs = []  # gen_outputs(gmf_df, crmodel, rng, mon)
    sids = gmf_df.sid.to_numpy()
    assets = assetcol.to_dframe()
    for taxo in assets.taxonomy.unique():
        adf = assets[assets.taxonomy == taxo]
        df = gmf_df[numpy.isin(sids, adf.site_id.unique())]
        if len(df) == 0:  # common enough
            continue
        out = crmodel.get_output(adf, df, oq._sec_losses, rng)
        outs.append(out)
    _avg, alt = aggreg(outs, crmodel, ARK, aggids, rlz_id, oq.ideduc, mon)
    del alt['event_id']
    del alt['variance']
    alt['type'] = LOSSTYPE[alt.loss_id]
    del alt['loss_id']
    alt['agg_keys'] = general.decode(agg_keys[alt.agg_id])
    del alt['agg_id']
    return alt


def size_mb(df):
    """
    :returns: the size in MB of the dataframe
    """
    return df.memory_usage().sum() / 1024**2


# Index the existing asset table in the order used to compute losses.
def _asset_rows_and_slices(assets):
    names = assets.dtype.names
    zeros = numpy.zeros(len(assets), U32)
    id0 = assets['ID_0'] if 'ID_0' in names else zeros
    id1 = assets['NAME_1'] if 'NAME_1' in names else zeros
    # NB: this is subtle! without the ordering by 'ordinal'
    # the assets will be ordered differently on AMD machines
    # with respect to Intel machines, depending on the machine, thus
    # causing different losses
    rows = numpy.lexsort((assets['ordinal'], id1, id0)).astype(U32)

    # building start-stop indices, so that the assets are read by region
    maxsize = int(config.memory.max_assets_chunk)
    id01 = (id0 * TWO16 + id1)[rows]
    iss = []
    for idx, start, stop in performance.idx_start_stop(id01):
        for slc in general.gen_slices(start, stop, maxsize):
            iss.append((idx, slc.start, slc.stop))
    return rows, U32(iss)


def fast_agg(keys, values, li, loss2):
    """
    :param keys: an array of N uint64 numbers encoding (event_id, agg_id)
    :param values: an array of (N, D) floats
    :param li: loss type index
    :param loss2: dictionary unique key -> array(L, D)
    """
    ukeys, avalues = general.fast_agg2(keys, values)
    for ukey, avalue in zip(ukeys, avalues):
        loss2[ukey][li] += avalue


def update(loss3, lti, X, alt, rlz_id, collect_rlzs):
    """
    Populate loss3 a dictionary {'aids': [], 'bids': [], 'loss': []}

    :param alt: DataFrame agg_loss_table
    :param rlz_id: effective realization index (usually 0)
    :param collect_rlzs: usually True
    """
    if collect_rlzs or len(numpy.unique(rlz_id)) == 1:
        # fast lane
        ldf = pandas.DataFrame(
            dict(aid=alt.aid.to_numpy(), loss=alt.loss.to_numpy()))
        tot = ldf.groupby('aid').loss.sum()
        aids = tot.index.to_numpy()
        # the single realization is 0 when collecting, else rlz_id[0]
        rlz = 0 if collect_rlzs else rlz_id[0]
        rlzs = numpy.full(len(tot), rlz, U32)
    else:
        # rare case
        ldf = pandas.DataFrame(
            dict(aid=alt.aid.to_numpy(), loss=alt.loss.to_numpy(),
                 rlz=rlz_id[U32(alt.eid)]))  # NB: without the U32 here
        # the SURA calculation would fail with alt.eid being F64 (?)
        tot = ldf.groupby(['aid', 'rlz']).loss.sum()
        aids, rlzs = zip(*tot.index)
        rlzs = U32(rlzs)
    loss3['aids'].append(U32(aids))
    loss3['bids'].append(rlzs * X + lti)
    loss3['loss'].append(F32(tot))


def debugprint(ln, asset_loss_table, adf):
    """
    Print risk_by_event in a reasonable format. To be used with --nd
    """
    if '+' in ln or ln == 'claim':
        df = asset_loss_table.set_index('aid').rename(columns={'loss': ln})
        df['asset_id'] = general.decode(adf.id[df.index].to_numpy())
        del df['variance']
        print(df)


def build_avg(loss3, A, X):
    """
    Build average losses as a sparse matrix of shape (A, X)
    """
    if loss3['aids']:
        aids = numpy.concatenate(loss3['aids'], dtype=U32)
        bids = numpy.concatenate(loss3['bids'], dtype=U32)
        loss = numpy.concatenate(loss3['loss'], dtype=F32)
        avg = sparse.coo_matrix((loss, (aids, bids)), (A, X))
    else:
        avg = sparse.coo_matrix((A, X), dtype=F32)
    return avg


def build_alt(loss2, xtypes, correl=False):
    """
    Build aggregated loss table
    """
    lis = range(len(xtypes))
    dic = general.AccumDict(accum=[])
    for ukey, arr in loss2.items():
        if correl:  # square after summing sigmas across all asset chunks
            arr = arr.copy()
            arr[:, 0] **= 2
        eid, kid = divmod(ukey, TWO32)
        for li in lis:
            if arr[li].any():
                dic['event_id'].append(eid)
                dic['agg_id'].append(kid)
                dic['loss_id'].append(LOSSID[xtypes[li]])
                for c, col in enumerate(['variance', 'loss']):
                    dic[col].append(arr[li, c])
    fix_dtypes(dic)
    return pandas.DataFrame(dic)


def aggreg(out, aggids, rlz_id, oq, loss2, loss3):
    """
    Update loss2 and loss3
    """
    correl = int(oq.asset_correlation)
    value_cols = ['variance', 'loss']
    xtypes = oq.xtypes
    for li, ln in enumerate(xtypes):
        if ln not in out or len(out[ln]) == 0:
            continue
        alt = out[ln]
        if oq.avg_losses:  # fast
            update(loss3, li, len(xtypes), alt, rlz_id, oq.collect_rlzs)
        if correl:  # use sigma^2 = (sum sigma_i)^2
            alt['variance'] = numpy.sqrt(alt.variance)
        eids = alt.eid.to_numpy() * TWO32  # U64
        values = numpy.array([alt[col] for col in value_cols]).T
        # aggregate all assets
        fast_agg(eids + U64(oq.K), values, li, loss2)
        if len(aggids):
            # aggregate assets for each tag combination
            aids = alt.aid.to_numpy()
            for kids in aggids[:, aids]:
                fast_agg(eids + U64(kids), values, li, loss2)


def _tot_loss_unit_consistency(units, total_losses, loss_types):
    total_losses_units = set()
    for separate_lt in total_losses.split('+'):
        assert separate_lt in loss_types, (separate_lt, loss_types)
        for unit, lt in zip(units, loss_types):
            if separate_lt == lt:
                total_losses_units.add(unit)
    if len(total_losses_units) != 1:
        logging.warning(
            'The units of the single components of the total losses'
            ' are not homogeneous: %s" ' % total_losses_units)


def set_oqparam(oq, assetcol, dstore):
    """
    Set the attributes .M, .K, .A, .ideduc, ._sec_losses
    """
    try:
        K = len(dstore['agg_keys'])
    except KeyError:
        K = 0
    sec_losses = []  # one insured loss for each loss type with a policy
    try:
        policy_df = dstore.read_df('policy')
    except KeyError:
        pass
    else:
        if 'reinsurance' not in oq.inputs:
            sec_losses.append(
                partial(insurance_losses, policy_df=policy_df))

    ideduc = assetcol['ideductible'].any()
    cc = dstore['exposure'].cost_calculator
    if oq.total_losses and oq.total_loss_types and cc.cost_types:
        # cc.cost_types is empty in scenario_damage/case_21 (consequences)
        units = cc.get_units(oq.total_loss_types)
        _tot_loss_unit_consistency(
            units.split(), oq.total_losses, oq.total_loss_types)
        sec_losses.append(
            partial(total_losses, kind=oq.total_losses, ideduc=ideduc))
    elif ideduc:
        # subtract the insurance deductible for a single loss_type
        [lt] = oq.loss_types
        sec_losses.append(partial(total_losses, kind=lt, ideduc=ideduc))

    oq._sec_losses = sec_losses
    oq.ideduc = int(ideduc)
    oq.M = len(oq.all_imts())
    oq.K = K
    oq.A = assetcol['ordinal'].max() + 1


# Open the file owning an inherited dataset, if it lives in a parent.
def _worker_source(h5, name):
    path = h5['_risk_worker'].attrs.get(name)
    if path is None:
        return nullcontext(h5)
    return hdf5.File(os.path.join(os.path.dirname(h5.filename), path), 'r')


# HDF5 point selection is expensive for long arrays of row numbers.
def _take_asset_rows(dset, rows):
    assets = numpy.empty(len(rows), dset.dtype)
    for _, start, stop in performance.idx_start_stop(rows // 4096):
        block = rows[start:stop]
        lo, hi = int(block.min()), int(block.max()) + 1
        assets[start:stop] = dset[lo:hi][block - lo]
    return assets


class AssetReader:
    """
    Read a slice of assets and measure time spent and memory allocated.
    """
    def __init__(self, h5, source, monitor):
        self.monitor = monitor('reading assets', measuremem=True)
        self.rows = h5.get('_risk_worker/asset_rows')
        self.assets = dset = source['assetcol/array']
        # The canonical asset array uses a fixed, contiguous layout. Map
        # its bytes read-only so scattered rows don't need HDF5 point I/O.
        offset = dset.id.get_offset()
        if offset is not None and not dset.dtype.hasobject:
            try:
                self.assets = numpy.memmap(
                    source.filename, dtype=dset.dtype, mode='r',
                    offset=offset, shape=dset.shape)
            except (OSError, ValueError):  # use ordinary HDF5 reads
                pass

    def read(self, s0, s1, active_sites):
        with self.monitor:
            if self.rows is not None and isinstance(self.assets, numpy.memmap):
                rows = self.rows[s0:s1]
                sids = self.assets['site_id'][rows]
                arr = self.assets[rows[active_sites[sids]]]
            else:
                if self.rows is None:
                    arr = self.assets[s0:s1]
                else:
                    arr = _take_asset_rows(self.assets, self.rows[s0:s1])
                arr = arr[active_sites[arr['site_id']]]
            cols = {name: arr[name] for name in arr.dtype.names
                    if name != 'id'}
            # Pack columns once so filtering does not scan strided records.
            return pandas.DataFrame(cols).set_index('ordinal')


def event_based_risk(gmf_df, monitor):
    """
    Aggregate the losses for all assets for the given event slice

    :returns: dictionary with keys 'alt', 'avg', 'gmf_bytes'
    """
    with (hdf5.File(monitor.filename, 'r') as h5,
          _worker_source(h5, 'asset_file') as assets):
        return _risk_from_gmfs(gmf_df, h5, assets, monitor)


# Read the worker inputs once per task, then process assets by region.
def _risk_from_gmfs(gmf_df, h5, assets, monitor):
    with monitor('reading crmodel', measuremem=True):
        crmodel = base.read_worker_model(h5)
    oq = crmodel.oqparam
    xtypes = oq.xtypes
    worker = h5['_risk_worker']
    R = int(worker.attrs['R'])
    X = len(xtypes)
    loss2 = general.AccumDict(accum=numpy.zeros((X, 2)))  # u8idx->array
    loss3 = {'aids': [], 'bids': [], 'loss': []}
    if os.environ.get('OQ_DEBUG_SITE'):
        print(gmf_df)

    aggids = worker['aggids'][:] if oq.K else ()
    rlz_id = ()
    if oq.avg_losses and not oq.collect_rlzs:
        with _worker_source(h5, 'events_file') as source:
            rlz_id = source['events'].fields('rlz_id')[:]
    areader = AssetReader(h5, assets, monitor)
    sids = gmf_df.sid.to_numpy()
    active = numpy.zeros(len(worker['num_assets']), bool)
    active[sids[sids < len(active)]] = True
    items = zip(worker['asset_slices'][:], worker['taxonomy_order'][:])
    if oq.ignore_master_seed or oq.ignore_covs:
        rng = None
    else:
        rng = MultiEventRNG(oq.master_seed, gmf_df.eid.unique(),
                            int(oq.asset_correlation))
    risk_mon = monitor('computing risk', measuremem=False)
    fil_mon = monitor('filtering GMFs', measuremem=False)
    agg_mon = monitor('aggregating losses', measuremem=False)
    try:
        countries = general.decode(assets['assetcol/tagcol/ID_0'][:])
    except KeyError:  # no ID_0 in the exposure
        countries = ["?"]  # assume a single country
    for (id01, s0, s1), taxonomies in items:
        adf_ = areader.read(s0, s1, active)
        if len(adf_) == 0:
            continue
        id0 = id01 // TWO16
        # The country selects the taxonomy mapping in multi-country impacts.
        try:
            country = countries[id0]
        except IndexError:
            raise IndexError(f'Index {id0} not in {countries}')
        with fil_mon:
            groups = adf_.groupby('taxonomy', sort=False).indices
        for taxo in taxonomies:
            with fil_mon:
                # filtering is *crucial* for the performance of the next step
                positions = groups.get(taxo)
                if positions is None:
                    continue
                adf = adf_.take(positions)
                gdf = gmf_df[numpy.isin(gmf_df.sid, adf.site_id.unique())]
            with risk_mon:
                [out] = crmodel.get_outputs(
                    adf, gdf, crmodel.oqparam._sec_losses, rng, country)
            with agg_mon:
                aggreg(out, aggids, rlz_id, oq, loss2, loss3)
    avg = build_avg(loss3, oq.A, R*X)
    alt = build_alt(loss2, xtypes, int(oq.asset_correlation))
    return dict(avg=avg, alt=alt, gmf_bytes=gmf_df.memory_usage().sum())


def ebrisk(allrups, cmakers, sids, secperils, dstore, monitor):
    """
    :param rups: list of ruptures with the same trt_smr
    :param cmakers: ContextMaker instances associated to each trt_smr
    :param sids: array of site indices
    :param secperils: list of secondary peril instances
    :param dstore: a DataStore instance
    :param monitor: a Monitor instance
    :yields: dictionaries with keys 'avg', 'alt' and 'gmfbytes'
    """
    oq = cmakers[0].oq
    oq.ground_motion_fields = True
    # NB: there is one dataframe per filtered rupture
    # NB: the times are kept also for the batches without GMFs, since
    # the record of a rupture can be in the last (empty) batch
    items = ((dic['gmfdata'], dic.get('times', ()))
             for dic in event_based.event_based(
                 allrups, cmakers, sids, secperils, dstore, monitor))
    with hdf5.File(monitor.filename, 'r') as h5:
        num_assets = h5['_risk_worker/num_assets'][:]
    for blk in general.block_splitter(
            items, AE_MAX, lambda item: num_assets[item[0].sid].sum()):
        times = [t for _, t in blk if len(t)]
        if times:
            yield dict(times=numpy.concatenate(times))
        dfs = [df for df, _ in blk if len(df)]
        if not dfs:
            continue
        # NB: it is essential to concatenate the small dataframes to have
        # long arrays (around AE_MAX) and hence a good performance
        ae = int(sum(num_assets[df.sid].sum() for df in dfs))
        if ae > AE_MAX:  # big task
            calc_id, task_no = monitor.calc_id, monitor.task_no
            print(f'{calc_id=}, {task_no=}, {ae=:_d}')
            yield event_based_risk, pandas.concat(dfs)
        else:
            yield event_based_risk(pandas.concat(dfs), monitor)


@performance.compile("(f4[:,:,:], i4[:], i4[:], f4[:], i8)")
def fast_add(avg_losses, row, col, data, X):
    for r, c, d in zip(row, col, data):
        rlz, lti = divmod(c, X)
        avg_losses[r, lti, rlz] += d


@base.calculators.add('scenario_risk', 'event_based_risk')
class EventBasedRiskCalculator(event_based.EventBasedCalculator):
    """
    Event based risk calculator generating event loss tables
    """
    core_task = ebrisk
    is_stochastic = True
    precalc = 'event_based'
    accept_precalc = ['scenario', 'event_based', 'event_based_risk']

    # Publish the risk worker inputs before enabling SWMR.
    def _prepare_worker_data(self):
        oq = self.oqparam
        dstore = self.datastore
        worker = base.prepare_risk_worker_data(
            dstore, self.crmodel, self.assetcol)
        rows, iss = _asset_rows_and_slices(self.assetcol.array)
        max_assets_per_region = (iss[:, 2] - iss[:, 1]).max()
        logging.info(f'{max_assets_per_region=:_d}')
        if not numpy.all(rows[1:] > rows[:-1]):
            worker['asset_rows'] = rows
        worker['num_assets'] = general.fast_agg(self.assetcol['site_id'])
        worker['asset_slices'] = iss
        # Keep the original taxonomy order so stochastic losses use the
        # same sequence of draws when assets without GMFs are skipped.
        taxonomy = self.assetcol['taxonomy']
        dstore.hdf5.save_vlen('_risk_worker/taxonomy_order', [
            pandas.unique(taxonomy[rows[s0:s1]]) for _, s0, s1 in iss])
        attrs = worker.attrs
        attrs['R'] = self.R
        sources = [('assetcol/array', 'asset_file')]
        if oq.avg_losses and not oq.collect_rlzs:
            sources.append(('events', 'events_file'))
        for key, name in sources:
            filename = dstore[key].file.filename
            if filename != dstore.filename:
                attrs[name] = os.path.relpath(
                    filename, os.path.dirname(dstore.filename))

    def pre_execute(self):
        oq = self.oqparam
        parent = self.datastore.parent
        if parent:
            self.datastore['full_lt'] = parent['full_lt']
            self.parent_events = ne = len(parent['events'])
            logging.info('There are %d ruptures and %d events',
                         len(parent['ruptures']), ne)
        else:
            self.parent_events = None
        super().pre_execute()
        parentdir = (os.path.dirname(self.datastore.ppath)
                     if self.datastore.ppath else None)
        oq.hdf5path = self.datastore.filename
        oq.parentdir = parentdir
        if 'events' in self.datastore:
            logging.info(
                'There are {:_d} ruptures and {:_d} events'.format(
                    len(self.datastore['ruptures']),
                    len(self.datastore['events'])))
        self.events_per_sid = numpy.zeros(self.N, U32)
        set_oqparam(oq, self.assetcol, self.datastore)
        self.A = A = len(self.assetcol)
        self.L = L = len(oq.loss_types)
        self.xtypes = oq.xtypes
        self.X = len(self.xtypes)
        ELT = len(oq.ext_loss_types)
        if oq.calculation_mode == 'event_based_risk' and oq.avg_losses:
            R = 1 if oq.collect_rlzs else self.R
            logging.info('Transfering %s * %d per task in avg_losses',
                         general.humansize(A * 8 * R), ELT)
            # NB: the size to check is the one transferred, i.e. with R
            if A * ELT * R * 8 > int(config.memory.avg_losses_max):
                if oq.collect_rlzs:
                    logging.warning('For large exposures consider setting '
                                    'avg_losses=false')
                else:
                    raise ValueError('For large exposures you must set '
                                     'collect_rlzs = true')
        if (oq.aggregate_by and (
                self.E * A > float(config.memory.max_potential_gmfs) and
                all(val == 0 for val in oq.minimum_asset_loss.values()))):
            logging.warning('The calculation is really big; consider setting '
                            'minimum_asset_loss')
        base.create_risk_by_event(self)
        self.gmf_bytes = 0
        self.rlzs = self.datastore['events']['rlz_id']
        self.num_events = numpy.bincount(self.rlzs, minlength=self.R)
        if oq.avg_losses:
            self.create_avg_losses()
        alt_nbytes = 4 * self.E * L
        if alt_nbytes / (oq.concurrent_tasks or 1) > TWO32:
            raise RuntimeError('The risk_by_event is too big to be transfer'
                               'ed with %d tasks' % oq.concurrent_tasks)

    def create_avg_losses(self):
        oq = self.oqparam
        R0 = oq.number_of_logic_tree_samples or len(
            base.get_weights(oq, self.datastore))
        R = 1 if oq.collect_rlzs else R0
        S = len(oq.hazard_stats())
        fix_investigation_time(oq, self.datastore)
        if oq.collect_rlzs:
            if oq.investigation_time:  # event_based
                self.avg_ratio = numpy.array([oq.time_ratio / R0])
            else:  # scenario
                self.avg_ratio = numpy.array([1. / self.num_events.sum()])
        else:
            if oq.investigation_time:  # event_based
                self.avg_ratio = numpy.array([oq.time_ratio] * R0)
            else:  # scenario
                self.avg_ratio = 1. / self.num_events
        self.avg_losses = numpy.zeros((self.A, self.X, R), F32)
        for lt in self.xtypes:
            self.datastore.create_dset(
                'avg_losses-rlzs/' + lt, F32, (self.A, R), 'gzip')
            if S and R > 1:
                self.datastore.create_dset(
                    'avg_losses-stats/' + lt, F32, (self.A, S), 'gzip')

    def execute(self):
        """
        Compute risk from GMFs or ruptures depending on what is stored
        """
        oq = self.oqparam
        if not oq.ground_motion_fields or 'gmf_data' not in self.datastore:
            # start from ruptures
            if (oq.ground_motion_fields and
                    not oq.hazard_calculation_id and
                    'gsim_logic_tree' not in oq.inputs and
                    oq.gsim == '[FromFile]'):
                raise InvalidFile('%s: missing gsim or gsim_logic_tree_file'
                                  % oq.inputs['job_ini'])
            elif oq.hazard_calculation_id is None and not hasattr(
                    oq, 'maximum_distance'):
                raise InvalidFile('Missing maximum_distance in %s'
                                  % oq.inputs['job_ini'])
            rup0 = self.datastore['ruptures'][0]
            if not hasattr(self, 'sec_perils'):
                self.add_sec_perils(oq)
            self.datastore.create_dset('ruptimes', event_based.rup_dt)
            self._prepare_worker_data()
            event_based.run(ebrisk, oq, rup0, self)
            if self.gmf_bytes == 0:
                logging.error(
                    'No GMFs were generated, perhaps they were '
                    'all below the minimum_intensity threshold')
                return 1
            self.datastore['/'].attrs['gmf_bytes'] = self.gmf_bytes
            logging.info(
                'Produced %s of GMFs', general.humansize(self.gmf_bytes))
        else:  # start from GMFs
            self._prepare_worker_data()
            smap, gmf_dfs = starmap_from_gmfs(
                event_based_risk, oq, self.datastore, self._monitor)
            for gmf_df in gmf_dfs:
                smap.submit((gmf_df,))
            smap.reduce(self.agg_dicts)

        if self.parent_events:
            assert self.parent_events == len(self.datastore['events'])
        return 1

    def log_info(self, eids):
        """
        Printing some information about the risk calculation
        """
        logging.info('Processing {:_d} rows of gmf_data'.format(len(eids)))
        E = len(numpy.unique(eids))
        K = self.oqparam.K
        logging.info('Risk parameters (rel_E={:_d}, K={:_d}, X={})'.
                     format(E, K, self.X))

    def agg_dicts(self, dummy, dic):
        """
        :param dummy: unused parameter
        :param dic: dictionary with keys "avg", "alt"
        """
        if not dic:
            return
        self.gmf_bytes += dic.pop('gmf_bytes', 0)
        self.oqparam.ground_motion_fields = False  # hack
        times = dic.pop('times', None)
        if times is not None:
            hdf5.extend(self.datastore['ruptimes'], times)
        alt = dic.pop('alt', None)
        if alt is not None:
            with self.monitor('saving risk_by_event'):
                for name in alt.columns:
                    dset = self.datastore['risk_by_event/' + name]
                    hdf5.extend(dset, alt[name].to_numpy())
        coo = dic.pop('avg', None)
        if coo is not None and self.oqparam.avg_losses:
            # avg_losses are stored as coo matrices
            with self.monitor('saving avg_losses'):
                # the non-numpy approach is 2-3x slower, causing
                # a big data queue and then running out of memory
                # rlzs, xlts = numpy.divmod(coo.col, self.X)
                # self.avg_losses[coo.row, xlts, rlzs] += coo.data
                fast_add(self.avg_losses, coo.row, coo.col, coo.data, self.X)

    def post_execute(self, dummy):
        """
        Compute and store average losses from the risk_by_event dataset,
        and then loss curves and maps.
        """
        oq = self.oqparam
        K = self.datastore['risk_by_event'].attrs.get('K', 0)
        upper_limit = self.E * (K + 1) * len(self.xtypes)
        if upper_limit < 1E7:
            # sanity check on risk_by_event if not too large
            alt = self.datastore.read_df('risk_by_event')
            size = len(alt)
            assert size <= upper_limit, (size, upper_limit)
            # sanity check on uniqueness by (agg_id, loss_id, event_id)
            arr = alt[['agg_id', 'loss_id', 'event_id']].to_numpy()
            uni, cnt = numpy.unique(arr, axis=0, return_counts=True)
            if len(uni) < len(arr):
                dupl = uni[cnt > 1]  # (agg_id, loss_id, event_id)
                raise RuntimeError(
                    'risk_by_event contains %d duplicates for event %s' %
                    (len(arr) - len(uni), dupl[0, 2]))

        s = oq.hazard_stats()
        if s:
            _statnames, statfuncs = zip(*s.items())
            weights = base.get_weights(oq, self.datastore)
        if oq.avg_losses:
            R = self.avg_losses.shape[2]
            for li, lt in enumerate(self.xtypes):
                al = self.avg_losses[:, li]  # shape (A, R)
                for r in range(R):
                    al[:, r] *= self.avg_ratio[r]
                name = 'avg_losses-rlzs/' + lt
                logging.info(f'Storing {name}')
                self.datastore[name][:] = al
                if s and self.R > 1:
                    self.datastore[name.replace('-rlzs', '-stats')][:] = \
                        stats.compute_stats2(al, statfuncs, weights)

        self.build_aggcurves()
        if oq.reaggregate_by:
            post_aggregate(self.datastore.calc_id,
                           ','.join(oq.reaggregate_by))

    def build_aggcurves(self):
        prc = PostRiskCalculator(self.oqparam, self.datastore.calc_id)
        prc.assetcol = self.assetcol
        if hasattr(self, 'exported'):
            prc.exported = self.exported
        prc.pre_execute()
        res = prc.execute()
        prc.post_execute(res)
