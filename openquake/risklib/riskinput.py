# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2016 GEM Foundation
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

import os
import operator
import logging
import tempfile
import collections

import numpy
import h5py

from openquake.baselib import hdf5
from openquake.baselib.python3compat import zip
from openquake.baselib.performance import Monitor
from openquake.baselib.general import groupby, split_in_blocks
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib import site
from openquake.risklib import scientific, riskmodels

U32 = numpy.uint32
F32 = numpy.float32

FIELDS = ('site_id', 'lon', 'lat', 'idx', 'taxonomy', 'area', 'number',
          'occupants', 'deductible~', 'insurance_limit~', 'retrofitted~')

by_taxonomy = operator.attrgetter('taxonomy')


class AssetCollection(object):
    D, I, R = len('deductible~'), len('insurance_limit~'), len('retrofitted~')

    def __init__(self, assets_by_site, cost_calculator, time_event,
                 time_events=''):
        self.cc = cost_calculator
        self.time_event = time_event
        self.time_events = time_events
        self.array, self.taxonomies = self.build_asset_collection(
            assets_by_site, time_event)
        fields = self.array.dtype.names
        self.loss_types = sorted(f for f in fields
                                 if not f.startswith(FIELDS))
        self.deduc = [n for n in fields if n.startswith('deductible~')]
        self.i_lim = [n for n in fields if n.startswith('insurance_limit~')]
        self.retro = [n for n in fields if n.startswith('retrofitted~')]

    def assets_by_site(self):
        """
        :returns: numpy array of lists with the assets by each site
        """
        assetcol = self.array
        site_ids = sorted(set(assetcol['site_id']))
        assets_by_site = [[] for sid in site_ids]
        index = dict(zip(site_ids, range(len(site_ids))))
        for i, ass in enumerate(assetcol):
            assets_by_site[index[ass['site_id']]].append(self[i])
        return numpy.array(assets_by_site)

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __getitem__(self, indices):
        if isinstance(indices, int):  # single asset
            a = self.array[indices]
            values = {lt: a[lt] for lt in self.loss_types}
            if 'occupants' in self.array.dtype.names:
                values['occupants_' + str(self.time_event)] = a['occupants']
            return riskmodels.Asset(
                    a['idx'],
                    self.taxonomies[a['taxonomy']],
                    number=a['number'],
                    location=(a['lon'], a['lat']),
                    values=values,
                    area=a['area'],
                    deductibles={lt[self.D:]: a[lt] for lt in self.deduc},
                    insurance_limits={lt[self.I:]: a[lt] for lt in self.i_lim},
                    retrofitteds={lt[self.R:]: a[lt] for lt in self.retro},
                    calc=self.cc, ordinal=indices)
        new = object.__new__(self.__class__)
        new.time_event = self.time_event
        new.array = self.array[indices]
        new.taxonomies = self.taxonomies
        return new

    def __len__(self):
        return len(self.array)

    def __toh5__(self):
        attrs = {'time_event': self.time_event or 'None',
                 'time_events': self.time_events,
                 'loss_types': self.loss_types,
                 'deduc': self.deduc, 'i_lim': self.i_lim, 'retro': self.retro,
                 'nbytes': self.array.nbytes}
        return dict(array=self.array, taxonomies=self.taxonomies,
                    cost_calculator=self.cc), attrs

    def __fromh5__(self, dic, attrs):
        vars(self).update(attrs)
        self.array = dic['array'].value
        self.taxonomies = dic['taxonomies'].value
        self.cc = dic['cost_calculator']

    @staticmethod
    def build_asset_collection(assets_by_site, time_event=None):
        """
        :param assets_by_site: a list of lists of assets
        :param time_event: a time event string (or None)
        :returns: two arrays `assetcol` and `taxonomies`
        """
        for assets in assets_by_site:
            if len(assets):
                first_asset = assets[0]
                break
        else:  # no break
            raise ValueError('There are no assets!')
        candidate_loss_types = list(first_asset.values)
        loss_types = []
        the_occupants = 'occupants_%s' % time_event
        for candidate in candidate_loss_types:
            if candidate.startswith('occupants'):
                if candidate == the_occupants:
                    loss_types.append('occupants')
                # discard occupants for different time periods
            else:
                loss_types.append(candidate)
        deductible_d = first_asset.deductibles or {}
        limit_d = first_asset.insurance_limits or {}
        retrofitting_d = first_asset.retrofitteds or {}
        deductibles = ['deductible~%s' % name for name in deductible_d]
        limits = ['insurance_limit~%s' % name for name in limit_d]
        retrofittings = ['retrofitted~%s' % n for n in retrofitting_d]
        float_fields = loss_types + deductibles + limits + retrofittings
        taxonomies = set()
        for assets in assets_by_site:
            for asset in assets:
                taxonomies.add(asset.taxonomy)
        sorted_taxonomies = sorted(taxonomies)
        asset_dt = numpy.dtype(
            [('idx', U32), ('lon', F32), ('lat', F32), ('site_id', U32),
             ('taxonomy', U32), ('number', F32), ('area', F32)] +
            [(name, float) for name in float_fields])
        num_assets = sum(len(assets) for assets in assets_by_site)
        assetcol = numpy.zeros(num_assets, asset_dt)
        asset_ordinal = 0
        fields = set(asset_dt.fields)
        for sid, assets_ in enumerate(assets_by_site):
            for asset in sorted(assets_, key=operator.attrgetter('id')):
                asset.ordinal = asset_ordinal
                record = assetcol[asset_ordinal]
                asset_ordinal += 1
                for field in fields:
                    if field == 'taxonomy':
                        value = sorted_taxonomies.index(asset.taxonomy)
                    elif field == 'number':
                        value = asset.number
                    elif field == 'area':
                        value = asset.area
                    elif field == 'idx':
                        value = asset.id
                    elif field == 'site_id':
                        value = sid
                    elif field == 'lon':
                        value = asset.location[0]
                    elif field == 'lat':
                        value = asset.location[1]
                    elif field == 'occupants':
                        value = asset.values[the_occupants]
                    else:
                        try:
                            name, lt = field.split('~')
                        except ValueError:  # no ~ in field
                            name, lt = 'value', field
                        # the line below retrieve one of `deductibles`,
                        # `insured_limits` or `retrofitteds` ("s" suffix)
                        value = getattr(asset, name + 's')[lt]
                    record[field] = value
        return assetcol, numpy.array(sorted_taxonomies, (bytes, 100))


class CompositeRiskModel(collections.Mapping):
    """
    A container (imt, taxonomy) -> riskmodel.

    :param riskmodels: a dictionary (imt, taxonomy) -> riskmodel
    :param damage_states: None or a list of damage states
    """
    def __init__(self, riskmodels, damage_states=None):
        self.damage_states = damage_states  # not None for damage calculations
        self._riskmodels = riskmodels
        self.loss_types = []
        self.curve_builders = []
        self.lti = {}  # loss_type -> idx
        self.covs = 0  # number of coefficients of variation
        self.taxonomies = []  # populated in get_risk_model

    def get_min_iml(self):
        iml = collections.defaultdict(list)
        for taxo, rm in self._riskmodels.items():
            for lt, rf in rm.risk_functions.items():
                iml[rf.imt].append(rf.imls[0])
        return {imt: min(iml[imt]) for imt in iml}

    def loss_type_dt(self, dtype=F32, insured=False):
        """
        Return a composite dtype based on the loss types
        """
        dts = [(lt, dtype) for lt in self.loss_types]
        if insured:
            for lt in self.loss_types:
                dts.append((lt + '_ins', dtype))
        return numpy.dtype(dts)

    def build_loss_dtypes(self, conditional_loss_poes, insured_losses=False):
        """
        :param conditional_loss_poes:
            configuration parameter
        :param insured_losses:
            configuration parameter
        :returns:
           loss_curve_dt and loss_maps_dt
        """
        lst = [('poe~%s' % poe, F32) for poe in conditional_loss_poes]
        if insured_losses:
            lst += [(name + '_ins', pair) for name, pair in lst]
        lm_dt = numpy.dtype(lst)
        lc_list = []
        lm_list = []
        for cb in (b for b in self.curve_builders if b.user_provided):
            pairs = [('losses', (F32, cb.curve_resolution)),
                     ('poes', (F32, cb.curve_resolution)),
                     ('avg', F32)]
            if insured_losses:
                pairs += [(name + '_ins', pair) for name, pair in pairs]
            lc_list.append((cb.loss_type, numpy.dtype(pairs)))
            lm_list.append((cb.loss_type, lm_dt))
        loss_curve_dt = numpy.dtype(lc_list) if lc_list else None
        loss_maps_dt = numpy.dtype(lm_list) if lm_list else None
        return loss_curve_dt, loss_maps_dt

    # FIXME: scheduled for removal once we change agg_curve to be built from
    # the user-provided loss ratios
    def build_all_loss_dtypes(self, curve_resolution, conditional_loss_poes,
                              insured_losses=False):
        """
        :param conditional_loss_poes:
            configuration parameter
        :param insured_losses:
            configuration parameter
        :returns:
           loss_curve_dt and loss_maps_dt
        """
        lst = [('poe~%s' % poe, F32) for poe in conditional_loss_poes]
        if insured_losses:
            lst += [(name + '_ins', pair) for name, pair in lst]
        lm_dt = numpy.dtype(lst)
        lc_list = []
        lm_list = []
        for loss_type in self.loss_types:
            pairs = [('losses', (F32, curve_resolution)),
                     ('poes', (F32, curve_resolution)),
                     ('avg', F32)]
            if insured_losses:
                pairs += [(name + '_ins', pair) for name, pair in pairs]
            lc_list.append((loss_type, numpy.dtype(pairs)))
            lm_list.append((loss_type, lm_dt))
        loss_curve_dt = numpy.dtype(lc_list) if lc_list else None
        loss_maps_dt = numpy.dtype(lm_list) if lm_list else None
        return loss_curve_dt, loss_maps_dt

    def make_curve_builders(self, oqparam):
        """
        Populate the inner lists .loss_types, .curve_builders.
        """
        default_loss_ratios = numpy.linspace(
            0, 1, oqparam.loss_curve_resolution + 1)[1:]
        loss_types = self._get_loss_types()
        for l, loss_type in enumerate(loss_types):
            if oqparam.calculation_mode in ('classical', 'classical_risk'):
                curve_resolutions = set()
                lines = []
                for key in sorted(self):
                    rm = self[key]
                    if loss_type in rm.loss_ratios:
                        ratios = rm.loss_ratios[loss_type]
                        curve_resolutions.add(len(ratios))
                        lines.append('%s %d' % (
                            rm.risk_functions[loss_type], len(ratios)))
                if len(curve_resolutions) > 1:
                    logging.info(
                        'Different num_loss_ratios:\n%s', '\n'.join(lines))
                cb = scientific.CurveBuilder(
                    loss_type, ratios, True,
                    oqparam.conditional_loss_poes, oqparam.insured_losses,
                    curve_resolution=max(curve_resolutions))
            elif loss_type in oqparam.loss_ratios:  # loss_ratios provided
                cb = scientific.CurveBuilder(
                    loss_type, oqparam.loss_ratios[loss_type], True,
                    oqparam.conditional_loss_poes, oqparam.insured_losses)
            else:  # no loss_ratios provided
                cb = scientific.CurveBuilder(
                    loss_type, default_loss_ratios, False,
                    oqparam.conditional_loss_poes, oqparam.insured_losses)
            self.curve_builders.append(cb)
            self.loss_types.append(loss_type)
            self.lti[loss_type] = l

    def get_loss_ratios(self):
        """
        :returns: a 1-dimensional composite array with loss ratios by loss type
        """
        lst = [('user_provided', numpy.bool)]
        for cb in self.curve_builders:
            lst.append((cb.loss_type, F32, len(cb.ratios)))
        loss_ratios = numpy.zeros(1, numpy.dtype(lst))
        for cb in self.curve_builders:
            loss_ratios['user_provided'] = cb.user_provided
            loss_ratios[cb.loss_type] = tuple(cb.ratios)
        return loss_ratios

    def _get_loss_types(self):
        """
        :returns: a sorted list with all the loss_types contained in the model
        """
        ltypes = set()
        for rm in self.values():
            ltypes.update(rm.loss_types)
        return sorted(ltypes)

    def __getitem__(self, taxonomy):
        return self._riskmodels[taxonomy]

    def __iter__(self):
        return iter(sorted(self._riskmodels))

    def __len__(self):
        return len(self._riskmodels)

    def get_imt_taxonomies(self, imt=None):
        """
        :returns: sorted list of pairs (imt, taxonomies)
        """
        imt_taxonomies = collections.defaultdict(set)
        for taxonomy, riskmodel in self.items():
            for loss_type, rf in sorted(riskmodel.risk_functions.items()):
                if imt is None or imt == rf.imt:
                    imt_taxonomies[rf.imt].add(riskmodel.taxonomy)
        return sorted(imt_taxonomies.items())

    def build_input(self, imt, hazards_by_site, assetcol, eps_dict):
        """
        :param imt: an Intensity Measure Type
        :param hazards_by_site: an array of hazards per each site
        :param assetcol: AssetCollection instance
        :param eps_dict: a dictionary of epsilons
        :returns: a :class:`RiskInput` instance
        """
        return RiskInput(self.get_imt_taxonomies(imt),
                         hazards_by_site, assetcol, eps_dict)

    def build_inputs_from_ruptures(
            self, sitecol, all_ruptures, trunc_level, correl_model,
            min_iml, eps, hint):
        """
        :param sitecol: a SiteCollection instance
        :param all_ruptures: the complete list of EBRupture instances
        :param trunc_level: the truncation level (or None)
        :param correl_model: the correlation model (or None)
        :param min_iml: dictionary of minimum IMLs
        :param eps: a matrix of epsilons of shape (N, E)
        :param hint: hint for how many blocks to generate

        Yield :class:`RiskInputFromRuptures` instances.
        """
        imt_taxonomies = self.get_imt_taxonomies()
        by_trt_id = operator.attrgetter('trt_id')
        for ses_ruptures in split_in_blocks(
                all_ruptures, hint or 1, key=by_trt_id):
            eids = []
            for sr in ses_ruptures:
                eids.extend(sr.events['eid'])
            yield RiskInputFromRuptures(
                imt_taxonomies, sitecol, ses_ruptures,
                trunc_level, correl_model, min_iml, eps[:, eids], eids)

    def gen_outputs(self, riskinputs, rlzs_assoc, monitor,
                    assetcol=None):
        """
        Group the assets per taxonomy and compute the outputs by using the
        underlying riskmodels. Yield the outputs generated as dictionaries
        out_by_lr.

        :param riskinputs: a list of riskinputs with consistent IMT
        :param rlzs_assoc: a RlzsAssoc instance
        :param monitor: a monitor object used to measure the performance
        :param assetcol: not None only for event based risk
        """
        mon_hazard = monitor('building hazard')
        mon_risk = monitor('computing risk')
        monitor.gmfbytes = 0
        assets_by_site = (None if assetcol is None
                          else assetcol.assets_by_site())
        for riskinput in riskinputs:
            with mon_hazard:
                # get assets, epsilons, hazard
                hazard_by_site = riskinput.get_hazard(
                    rlzs_assoc, mon_hazard(measuremem=False))
            # compute the outputs with the appropriate riskmodels
            if assets_by_site is None:  # distribution by asset
                with mon_risk:
                    for assets, hazard in zip(
                            riskinput.assets_by_site, hazard_by_site):
                        the_assets = groupby(assets, by_taxonomy)
                        for taxonomy, assets in the_assets.items():
                            riskmodel = self[taxonomy]
                            epsgetter = riskinput.epsilon_getter(
                                [asset.ordinal for asset in assets])
                            for imt, taxonomies in riskinput.imt_taxonomies:
                                if taxonomy in taxonomies:
                                    yield riskmodel.out_by_lr(
                                        imt, assets, hazard[imt], epsgetter)
            else:  # event based, distribution by rupture
                try:
                    for out_by_lr in self.gen_out_by_lr(
                            riskinput, assets_by_site,
                            hazard_by_site, mon_risk):
                        yield out_by_lr
                finally:
                    # store the size of the temporary file and remove it
                    monitor.gmfbytes += hazard_by_site.close()

    def gen_out_by_lr(self, riskinput, assets_by_site, hazard_by_site,
                      mon_risk):
        """
        Yield the outputs by loss type and realization for each site id,
        asset and intensity measure type.
        """
        mon_hazard = mon_risk('getting hazard', measuremem=False)
        for sid, assets in enumerate(assets_by_site):
            with mon_hazard:
                hazard = hazard_by_site[sid]
            if not hazard:
                continue
            with mon_risk:
                for asset in assets:
                    epsgetter = riskinput.epsilon_getter([asset.ordinal])
                    for imt, taxonomies in riskinput.imt_taxonomies:
                        if asset.taxonomy in taxonomies:
                            yield self[asset.taxonomy].out_by_lr(
                                imt, [asset], hazard[imt], epsgetter)

    def __repr__(self):
        lines = ['%s: %s' % item for item in sorted(self.items())]
        return '<%s(%d, %d)\n%s>' % (
            self.__class__.__name__, len(lines), self.covs, '\n'.join(lines))


class RiskInput(object):
    """
    Contains all the assets and hazard values associated to a given
    imt and site.

    :param imt_taxonomies: a pair (IMT, taxonomies)
    :param hazard_by_site: array of hazards, one per site
    :param assets_by_site: array of assets, one per site
    :param eps_dict: dictionary of epsilons
    """
    def __init__(self, imt_taxonomies, hazard_by_site, assets_by_site,
                 eps_dict):
        if not imt_taxonomies:
            self.weight = 0
            return
        [(self.imt, taxonomies)] = imt_taxonomies
        self.hazard_by_site = hazard_by_site
        self.assets_by_site = [
            [a for a in assets if a.taxonomy in taxonomies]
            for assets in assets_by_site]
        taxonomies_set = set()
        self.weight = 0
        for assets in self.assets_by_site:
            for asset in assets:
                taxonomies_set.add(asset.taxonomy)
            self.weight += len(assets)
        self.taxonomies = sorted(taxonomies_set)
        self.eids = None  # for API compatibility with RiskInputFromRuptures
        self.eps = eps_dict

    @property
    def imt_taxonomies(self):
        """Return a list of pairs (imt, taxonomies) with a single element"""
        return [(self.imt, self.taxonomies)]

    def epsilon_getter(self, asset_ordinals):
        """
        :param asset_ordina: ordinal of the asset
        :returns: a closure returning an array of epsilons from the event IDs
        """
        return lambda _: [self.eps[aid] for aid in asset_ordinals]

    def get_hazard(self, rlzs_assoc, monitor=Monitor()):
        """
        :param rlzs_assoc:
            :class:`openquake.commonlib.source.RlzsAssoc` instance
        :param monitor:
            a :class:`openquake.baselib.performance.Monitor` instance
        :returns:
            list of hazard dictionaries imt -> rlz -> haz per each site
        """
        return [{self.imt: rlzs_assoc.combine(hazard)}
                for hazard in self.hazard_by_site]

    def __repr__(self):
        return '<%s IMT=%s, taxonomy=%s, weight=%d>' % (
            self.__class__.__name__, self.imt, ', '.join(self.taxonomies),
            self.weight)


def make_eps(assets_by_site, num_samples, seed, correlation):
    """
    :param assets_by_site: a list of lists of assets
    :param int num_samples: the number of ruptures
    :param int seed: a random seed
    :param float correlation: the correlation coefficient
    :returns: epsilons matrix of shape (num_assets, num_samples)
    """
    all_assets = (a for assets in assets_by_site for a in assets)
    assets_by_taxo = groupby(all_assets, by_taxonomy)
    num_assets = sum(map(len, assets_by_site))
    eps = numpy.zeros((num_assets, num_samples), numpy.float32)
    for taxonomy, assets in assets_by_taxo.items():
        # the association with the epsilons is done in order
        assets.sort(key=operator.attrgetter('id'))
        shape = (len(assets), num_samples)
        logging.info('Building %s epsilons for taxonomy %s', shape, taxonomy)
        zeros = numpy.zeros(shape)
        epsilons = scientific.make_epsilons(zeros, seed, correlation)
        for asset, epsrow in zip(assets, epsilons):
            eps[asset.ordinal] = epsrow
    return eps


# this not used; it could be used in the future, if we find computations
# that run out of memory. For now it is not used for two reasons:
# 1) it is slower than keeping everything in memory
# 2) it requires having disk space on the workers, which apparently is
# not the case for some sponsors
class _GmfCollector(object):
    """
    An object storing the GMFs into a temporary HDF5 file to save memory.
    """
    def __init__(self, calc_id, task_no, imts, rlzs):
        self.calc_id = calc_id
        self.task_no = task_no
        self.imts = imts
        self.rlzs = rlzs
        self.fname = os.path.join(
            tempfile.gettempdir(), '%d-%d.hdf5' % (calc_id, task_no))
        self.hdf5 = h5py.File(self.fname, 'w')

    def close(self):
        self.hdf5.close()
        nbytes = os.path.getsize(self.fname)
        os.remove(self.fname)
        return nbytes

    def save(self, sid, imt, rlz, gmvs, eids):
        key = '%s/%s/%s' % (sid, imt, rlz.ordinal)
        try:
            dset = self.hdf5[key]
        except KeyError:
            dset = self.hdf5.create_dataset(
                key, (0,), gmv_eid_dt, chunks=True, maxshape=(None,))
        hdf5.extend(dset, numpy.array(list(zip(gmvs, eids)), gmv_eid_dt))

    def __getitem__(self, sid):
        hazard = {}
        try:
            dset = self.hdf5[str(sid)]
        except KeyError:
            return hazard
        for imt in self.imts:
            try:
                items = dset[imt].items()
            except KeyError:
                hazard[imt] = {}
            else:
                hazard[imt] = {self.rlzs[int(rlzi)]: ds.value
                               for rlzi, ds in items}
        return hazard

gmv_eid_dt = numpy.dtype([('gmv', F32), ('eid', U32)])


class GmfCollector(object):
    """
    An object storing the GMFs in memory.
    """
    def __init__(self, imts, rlzs):
        self.imts = imts
        self.rlzs = rlzs
        self.dic = collections.defaultdict(list)
        self.nbytes = 0

    def close(self):
        self.dic.clear()
        return self.nbytes

    def save(self, sid, imt, rlz, gmvs, eids):
        key = '%s/%s/%s' % (sid, imt, rlz.ordinal)
        array = numpy.array(list(zip(gmvs, eids)), gmv_eid_dt)
        self.dic[key].append(array)
        self.nbytes += array.nbytes

    def __getitem__(self, sid):
        hazard = {}
        for imt in self.imts:
            hazard[imt] = {}
            for rlz in self.rlzs:
                key = '%s/%s/%s' % (sid, imt, rlz.ordinal)
                try:
                    data = self.dic[key]
                except KeyError:
                    pass
                else:
                    if data:
                        hazard[imt][rlz] = numpy.concatenate(data)
        return hazard


def calc_gmfs(eb_ruptures, sitecol, imts, rlzs_assoc,
              trunc_level, correl_model, min_iml, monitor=Monitor()):
    """
    :param eb_ruptures: a list of EBRuptures with the same trt_model_id
    :param sitecol: a SiteCollection instance
    :param imts: list of IMT strings
    :param rlzs_assoc: a RlzsAssoc instance
    :param trunc_level: truncation level
    :param correl_model: correlation model instance
    :param min_iml: a dictionary of minimum intensity measure levels
    :param monitor: a monitor instance
    :returns: a dictionary rlzi -> gmv_dt array
    """
    trt_id = eb_ruptures[0].trt_id
    gsims = rlzs_assoc.gsims_by_trt_id[trt_id]
    rlzs_by_gsim = rlzs_assoc.get_rlzs_by_gsim(trt_id)
    rlzs = rlzs_assoc.realizations
    ctx_mon = monitor('make contexts')
    gmf_mon = monitor('compute poes')
    sites = sitecol.complete
    gmfcoll = GmfCollector(imts, rlzs)
    for ebr in eb_ruptures:
        with ctx_mon:
            r_sites = site.FilteredSiteCollection(ebr.indices, sites)
            computer = GmfComputer(
                ebr.rupture, r_sites, imts, gsims,
                trunc_level, correl_model)
        with gmf_mon:
            ddic = computer.calcgmfs(
                ebr.multiplicity, ebr.rupture.seed, rlzs_by_gsim)
            for rlz, gmf_by_imt in ddic.items():
                for imt, gmf in gmf_by_imt.items():
                    for sid, gmvs in zip(r_sites.sids, gmf):
                        if min_iml:
                            ok = gmvs >= min_iml[imt]
                            gmvs, eids = gmvs[ok], ebr.eids[ok]
                        else:
                            eids = ebr.eids
                        if len(eids):
                            gmfcoll.save(sid, imt, rlz, gmvs, eids)
    return gmfcoll


class RiskInputFromRuptures(object):
    """
    Contains all the assets associated to the given IMT and a subsets of
    the ruptures for a given calculation.

    :param imt_taxonomies: list given by the risk model
    :param sitecol: SiteCollection instance
    :param assets_by_site: list of list of assets
    :param ses_ruptures: ordered array of EBRuptures
    :param gsims: list of GSIM instances
    :param trunc_level: truncation level for the GSIMs
    :param correl_model: correlation model for the GSIMs
    :params eps: a matrix of epsilons
    """
    def __init__(self, imt_taxonomies, sitecol, ses_ruptures,
                 trunc_level, correl_model, min_iml, epsilons, eids):
        self.imt_taxonomies = imt_taxonomies
        self.sitecol = sitecol
        self.ses_ruptures = numpy.array(ses_ruptures)
        self.trt_id = ses_ruptures[0].trt_id
        self.trunc_level = trunc_level
        self.correl_model = correl_model
        self.min_iml = min_iml
        self.weight = sum(sr.multiplicity for sr in ses_ruptures)
        self.imts = sorted(set(imt for imt, _ in imt_taxonomies))
        self.eids = eids  # E events
        self.eps = epsilons  # matrix N x E, events in this block

    def epsilon_getter(self, asset_ordinals):
        """
        :param asset_ordina: ordinal of the asset
        :returns: a closure returning an array of epsilons from the event IDs
        """
        eps = self.eps[asset_ordinals[0]]  # assume there is only one ordinal
        eid2eps = dict(zip(self.eids, eps))
        return lambda eids: numpy.array([eid2eps[eid] for eid in eids])

    def get_hazard(self, rlzs_assoc, monitor=Monitor()):
        """
        :param rlzs_assoc:
            :class:`openquake.commonlib.source.RlzsAssoc` instance
        :param monitor:
            a :class:`openquake.baselib.performance.Monitor` instance
        :returns:
            lists of N hazard dictionaries imt -> rlz -> Gmvs
        """
        hazards = calc_gmfs(
            self.ses_ruptures, self.sitecol, self.imts, rlzs_assoc,
            self.trunc_level, self.correl_model, self.min_iml, monitor)
        return hazards

    def __repr__(self):
        return '<%s IMT_taxonomies=%s, weight=%d>' % (
            self.__class__.__name__, self.imt_taxonomies, self.weight)
