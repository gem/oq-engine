# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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

import operator
import logging
import collections
import numpy

from openquake.baselib import hdf5
from openquake.baselib.python3compat import zip, decode
from openquake.baselib.general import groupby, get_array, AccumDict
from openquake.hazardlib import site, calc, valid
from openquake.risklib import scientific, riskmodels


class ValidationError(Exception):
    pass

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
U64 = numpy.uint64
TWO48 = 2 ** 48
EVENTS = -2
NBYTES = -1

FIELDS = ('site_id', 'lon', 'lat', 'idx', 'taxonomy_id', 'area', 'number',
          'occupants', 'deductible-', 'insurance_limit-', 'retrofitted-')

by_taxonomy = operator.attrgetter('taxonomy')


class Output(object):
    """
    A container for the losses of the assets on the given site ID for
    the given realization ordinal.
    """
    def __init__(self, loss_types, assets, values, sid, rlzi):
        self.loss_types = loss_types
        self.assets = assets
        self.values = values
        self.sid = sid
        self.r = rlzi

    def __getitem__(self, l):
        return self.values[l]


def get_refs(assets, hdf5path):
    """
    Debugging method returning the string IDs of the assets from the datastore
    """
    with hdf5.File(hdf5path, 'r') as f:
        return f['asset_refs'][[a.idx for a in assets]]


class AssetCollection(object):
    D, I, R = len('deductible-'), len('insurance_limit-'), len('retrofitted-')

    def __init__(self, assets_by_site, cost_calculator, time_event,
                 time_events=''):
        self.cc = cost_calculator
        self.time_event = time_event
        self.time_events = time_events
        self.tot_sites = len(assets_by_site)
        self.array, self.taxonomies = self.build_asset_collection(
            assets_by_site, time_event)
        fields = self.array.dtype.names
        self.loss_types = [f[6:] for f in fields if f.startswith('value-')]
        if 'occupants' in fields:
            self.loss_types.append('occupants')
        self.loss_types.sort()
        self.deduc = [n for n in fields if n.startswith('deductible-')]
        self.i_lim = [n for n in fields if n.startswith('insurance_limit-')]
        self.retro = [n for n in fields if n.startswith('retrofitted-')]

    def assets_by_site(self):
        """
        :returns: numpy array of lists with the assets by each site
        """
        assets_by_site = [[] for sid in range(self.tot_sites)]
        for i, ass in enumerate(self.array):
            assets_by_site[ass['site_id']].append(self[i])
        return numpy.array(assets_by_site)

    def values(self):
        """
        :returns: a composite array of asset values by loss type
        """
        loss_dt = numpy.dtype([(str(lt), F32) for lt in self.loss_types])
        vals = numpy.zeros(len(self), loss_dt)  # asset values by loss_type
        for assets in self.assets_by_site():
            for asset in assets:
                for ltype in self.loss_types:
                    vals[ltype][asset.ordinal] = asset.value(
                        ltype, self.time_event)
        return vals

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __getitem__(self, indices):
        if isinstance(indices, int):  # single asset
            a = self.array[indices]
            values = {lt: a['value-' + lt] for lt in self.loss_types
                      if lt != 'occupants'}
            if 'occupants' in self.array.dtype.names:
                values['occupants_' + str(self.time_event)] = a['occupants']
            return riskmodels.Asset(
                    a['idx'],
                    self.taxonomies[a['taxonomy_id']],
                    number=a['number'],
                    location=(valid.longitude(a['lon']),  # round coordinates
                              valid.latitude(a['lat'])),
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
        # NB: the loss types do not contain spaces, so we can store them
        # together as a single space-separated string
        attrs = {'time_event': self.time_event or 'None',
                 'time_events': ' '.join(map(decode, self.time_events)),
                 'loss_types': ' '.join(self.loss_types),
                 'deduc': ' '.join(self.deduc),
                 'i_lim': ' '.join(self.i_lim),
                 'retro': ' '.join(self.retro),
                 'tot_sites': self.tot_sites,
                 'nbytes': self.array.nbytes}
        return dict(array=self.array, taxonomies=self.taxonomies,
                    cost_calculator=self.cc), attrs

    def __fromh5__(self, dic, attrs):
        for name in ('time_events', 'loss_types', 'deduc', 'i_lim', 'retro'):
            setattr(self, name, attrs[name].split())
        self.time_event = attrs['time_event']
        self.tot_sites = attrs['tot_sites']
        self.nbytes = attrs['nbytes']
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
                loss_types.append('value-' + candidate)
        deductible_d = first_asset.deductibles or {}
        limit_d = first_asset.insurance_limits or {}
        retrofitting_d = first_asset.retrofitteds or {}
        deductibles = ['deductible-%s' % name for name in deductible_d]
        limits = ['insurance_limit-%s' % name for name in limit_d]
        retrofittings = ['retrofitted-%s' % n for n in retrofitting_d]
        float_fields = loss_types + deductibles + limits + retrofittings
        taxonomies = set()
        for assets in assets_by_site:
            for asset in assets:
                taxonomies.add(asset.taxonomy)
        sorted_taxonomies = sorted(taxonomies)
        asset_dt = numpy.dtype(
            [('idx', U32), ('lon', F32), ('lat', F32), ('site_id', U32),
             ('taxonomy_id', U32), ('number', F32), ('area', F32)] + [
                 (str(name), float) for name in float_fields])
        num_assets = sum(len(assets) for assets in assets_by_site)
        assetcol = numpy.zeros(num_assets, asset_dt)
        asset_ordinal = 0
        fields = set(asset_dt.fields)
        for sid, assets_ in enumerate(assets_by_site):
            for asset in sorted(assets_, key=operator.attrgetter('idx')):
                asset.ordinal = asset_ordinal
                record = assetcol[asset_ordinal]
                asset_ordinal += 1
                for field in fields:
                    if field == 'taxonomy_id':
                        value = sorted_taxonomies.index(asset.taxonomy)
                    elif field == 'number':
                        value = asset.number
                    elif field == 'area':
                        value = asset.area
                    elif field == 'idx':
                        value = asset.idx
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
                            name, lt = field.split('-')
                        except ValueError:  # no - in field
                            name, lt = 'value', field
                        # the line below retrieve one of `deductibles`,
                        # `insured_limits` or `retrofitteds` ("s" suffix)
                        value = getattr(asset, name + 's')[lt]
                    record[field] = value
        return assetcol, numpy.array(sorted_taxonomies, hdf5.vstr)


def read_composite_risk_model(dstore):
    """
    :param dstore: a DataStore instance
    :returns: a :class:`CompositeRiskModel` instance
    """
    oqparam = dstore['oqparam']
    crm = dstore.getitem('composite_risk_model')
    rmdict, retrodict = {}, {}
    for taxo, rm in crm.items():
        rmdict[taxo] = {}
        retrodict[taxo] = {}
        for lt in rm:
            lt = str(lt)  # ensure Python 2-3 compatibility
            rf = dstore['composite_risk_model/%s/%s' % (taxo, lt)]
            if lt.endswith('_retrofitted'):
                # strip _retrofitted, since len('_retrofitted') = 12
                retrodict[taxo][lt[:-12]] = rf
            else:
                rmdict[taxo][lt] = rf
    return CompositeRiskModel(oqparam, rmdict, retrodict)


class CompositeRiskModel(collections.Mapping):
    """
    A container (imt, taxonomy) -> riskmodel

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param rmdict:
        a dictionary (imt, taxonomy) -> loss_type -> risk_function
    """
    def __init__(self, oqparam, rmdict, retrodict):
        self.damage_states = []
        self._riskmodels = {}

        if getattr(oqparam, 'limit_states', []):
            # classical_damage/scenario_damage calculator
            if oqparam.calculation_mode in ('classical', 'scenario'):
                # case when the risk files are in the job_hazard.ini file
                oqparam.calculation_mode += '_damage'
            self.damage_states = ['no_damage'] + oqparam.limit_states
            delattr(oqparam, 'limit_states')
            for taxonomy, ffs_by_lt in rmdict.items():
                self._riskmodels[taxonomy] = riskmodels.get_riskmodel(
                    taxonomy, oqparam, fragility_functions=ffs_by_lt)
        elif oqparam.calculation_mode.endswith('_bcr'):
            # classical_bcr calculator
            for (taxonomy, vf_orig), (taxonomy_, vf_retro) in \
                    zip(rmdict.items(), retrodict.items()):
                assert taxonomy == taxonomy_  # same imt and taxonomy
                self._riskmodels[taxonomy] = riskmodels.get_riskmodel(
                    taxonomy, oqparam,
                    vulnerability_functions_orig=vf_orig,
                    vulnerability_functions_retro=vf_retro)
        else:
            # classical, event based and scenario calculators
            for taxonomy, vfs in rmdict.items():
                for vf in vfs.values():
                    # set the seed; this is important for the case of
                    # VulnerabilityFunctionWithPMF
                    vf.seed = oqparam.random_seed
                    self._riskmodels[taxonomy] = riskmodels.get_riskmodel(
                        taxonomy, oqparam, vulnerability_functions=vfs)

        self.init(oqparam)

    def init(self, oqparam):
        self.lti = {}  # loss_type -> idx
        self.covs = 0  # number of coefficients of variation
        self.curve_builder = self.make_curve_builder(oqparam)
        self.loss_types = [cb.loss_type for cb in self.curve_builder]
        self.insured_losses = oqparam.insured_losses
        expected_loss_types = set(self.loss_types)
        taxonomies = set()
        for taxonomy, riskmodel in self._riskmodels.items():
            taxonomies.add(taxonomy)
            riskmodel.compositemodel = self
            # save the number of nonzero coefficients of variation
            for vf in riskmodel.risk_functions.values():
                if hasattr(vf, 'covs') and vf.covs.any():
                    self.covs += 1
            missing = expected_loss_types - set(riskmodel.risk_functions)
            if missing:
                raise ValidationError(
                    'Missing vulnerability function for taxonomy %s and loss'
                    ' type %s' % (taxonomy, ', '.join(missing)))
        self.taxonomies = sorted(taxonomies)

    def get_min_iml(self):
        iml = collections.defaultdict(list)
        for taxo, rm in self._riskmodels.items():
            for lt, rf in rm.risk_functions.items():
                iml[rf.imt].append(rf.imls[0])
        return {imt: min(iml[imt]) for imt in iml}

    def make_curve_builder(self, oqparam):
        # NB: populate the inner lists .loss_types too
        cbs = []
        default_loss_ratios = numpy.linspace(
            0, 1, oqparam.loss_curve_resolution + 1)[1:]
        loss_types = self._get_loss_types()
        ses_ratio = oqparam.ses_ratio if oqparam.calculation_mode in (
            'event_based_risk',) else 1
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
                if len(curve_resolutions) > 1:  # example in test_case_5
                    logging.info(
                        'Different num_loss_ratios:\n%s', '\n'.join(lines))
                cb = scientific.LossTypeCurveBuilder(
                    loss_type, max(curve_resolutions), ratios, ses_ratio,
                    True, oqparam.conditional_loss_poes,
                    oqparam.insured_losses)
            elif loss_type in oqparam.loss_ratios:  # loss_ratios provided
                cb = scientific.LossTypeCurveBuilder(
                    loss_type, oqparam.loss_curve_resolution,
                    oqparam.loss_ratios[loss_type], ses_ratio, True,
                    oqparam.conditional_loss_poes, oqparam.insured_losses)
            else:  # no loss_ratios provided
                cb = scientific.LossTypeCurveBuilder(
                    loss_type, oqparam.loss_curve_resolution,
                    default_loss_ratios, ses_ratio, False,
                    oqparam.conditional_loss_poes, oqparam.insured_losses)
            cbs.append(cb)
            cb.index = l
            self.lti[loss_type] = l
        return scientific.CurveBuilder(
            cbs, oqparam.insured_losses, oqparam.conditional_loss_poes)

    def get_loss_ratios(self):
        """
        :returns: a 1-dimensional composite array with loss ratios by loss type
        """
        lst = [('user_provided', numpy.bool)]
        for cb in self.curve_builder:
            lst.append((cb.loss_type, F32, len(cb.ratios)))
        loss_ratios = numpy.zeros(1, numpy.dtype(lst))
        for cb in self.curve_builder:
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

    def gen_outputs(self, riskinput, monitor, assetcol=None):
        """
        Group the assets per taxonomy and compute the outputs by using the
        underlying riskmodels. Yield the outputs generated as dictionaries
        out_by_lr.

        :param riskinput: a RiskInput instance
        :param monitor: a monitor object used to measure the performance
        :param assetcol: not None only for event based risk
        """
        mon_context = monitor('building context')
        mon_hazard = monitor('building hazard')
        mon_risk = monitor('computing risk', measuremem=False)
        hazard_getter = riskinput.hazard_getter
        with mon_context:
            if assetcol is None:
                assets_by_site = riskinput.assets_by_site
            else:
                assets_by_site = assetcol.assets_by_site()

        # group the assets by taxonomy
        taxonomies = set()
        dic = collections.defaultdict(list)
        for sid, assets in enumerate(assets_by_site):
            group = groupby(assets, by_taxonomy)
            for taxonomy in group:
                epsgetter = riskinput.epsilon_getter(
                    [asset.ordinal for asset in group[taxonomy]])
                dic[taxonomy].append((sid, group[taxonomy], epsgetter))
                taxonomies.add(taxonomy)
        imti = {imt: i for i, imt in enumerate(hazard_getter.imts)}
        for gsim in hazard_getter.rlzs_by_gsim:
            with mon_hazard:
                hazard = hazard_getter.get_hazard(gsim)
            for r, rlz in enumerate(hazard_getter.rlzs_by_gsim[gsim]):
                hazardr = hazard[r]
                for taxonomy in sorted(taxonomies):
                    riskmodel = self[taxonomy]
                    with mon_risk:
                        for sid, assets, epsgetter in dic[taxonomy]:
                            outs = [None] * len(self.lti)
                            for lt in self.loss_types:
                                imt = riskmodel.risk_functions[lt].imt
                                haz = hazardr[sid, imti[imt]]
                                if len(haz):
                                    out = riskmodel(lt, assets, haz, epsgetter)
                                    outs[self.lti[lt]] = out
                            yield Output(self.loss_types, assets, outs,
                                         sid, rlz.ordinal)

        if hasattr(hazard_getter, 'gmdata'):  # for event based risk
            riskinput.gmdata = hazard_getter.gmdata

    def __toh5__(self):
        loss_types = hdf5.array_of_vstr(self._get_loss_types())
        return self._riskmodels, dict(covs=self.covs, loss_types=loss_types)

    def __repr__(self):
        lines = ['%s: %s' % item for item in sorted(self.items())]
        return '<%s(%d, %d)\n%s>' % (
            self.__class__.__name__, len(lines), self.covs, '\n'.join(lines))


class HazardGetter(object):
    """
    :param kind:
        kind of HazardGetter; can be 'poe' or 'gmf'
    :param grp_id:
        source group ID
    :param rlzs_by_gsim:
        a dictionary gsim -> realizations for that GSIM
    :param hazards_by_rlz:
        a nested dictionary rlz -> imt -> PoE array or a flat dictionary
        rlz -> GMF array of shape (N, I, E)
    :params sids:
        array of site IDs of interest
    :param imts:
        a list of IMT strings
    """
    def __init__(self, kind, grp_id, rlzs_by_gsim, hazards_by_rlz, sids, imts):
        assert kind in ('poe', 'gmf'), kind
        self.kind = kind
        self.grp_id = grp_id
        self.rlzs_by_gsim = rlzs_by_gsim
        self.sids = sids
        self.imts = imts
        self.data = {}
        for gsim in rlzs_by_gsim:
            rlzs = self.rlzs_by_gsim[gsim]
            self.data[gsim] = []
            for r, rlz in enumerate(rlzs):
                datadict = collections.defaultdict(list)
                self.data[gsim].append(datadict)
                hazards_by_imt = hazards_by_rlz[rlz]
                for imti, imt in enumerate(self.imts):
                    if kind == 'poe':
                        hazard_by_site = hazards_by_imt[imt][self.sids]
                    else:  # gmf
                        hazard_by_site = hazards_by_imt[self.sids, imti]
                    for idx, haz in enumerate(hazard_by_site):
                        datadict[idx, imti] = haz

        if kind == 'gmf':
            # now some attributes set for API compatibility with the GmfGetter
            # number of ground motion fields
            num_events = hazard_by_site.shape[-1]
            self.eids = numpy.arange(num_events, dtype=F32)
            # dictionary rlzi -> array(imts, events, nbytes)
            self.gmdata = AccumDict(accum=numpy.zeros(len(self.imts) + 2, F32))

    def init(self):  # for API compatibility
        pass

    def get_hazard(self, gsim):
        """
        :param gsim: a GSIM instance
        :returns: a list of dictionaries (num_sites, num_imts)
        """
        return self.data[gsim]


gmv_dt = numpy.dtype([('sid', U32), ('eid', U64), ('imti', U8), ('gmv', F32)])
gmf_data_dt = numpy.dtype([('rlzi', U16), ('sid', U32), ('eid', U64),
                           ('imti', U8), ('gmv', F32)])
BYTES_PER_RECORD = gmf_data_dt.itemsize


class GmfGetter(object):
    """
    An hazard getter with methods .gen_gmv and .get_hazard returning
    ground motion values.
    """
    def __init__(self, grp_id, rlzs_by_gsim, ebruptures, sitecol, imts,
                 min_iml, truncation_level, correlation_model, samples):
        assert sitecol is sitecol.complete
        self.grp_id = grp_id
        self.rlzs_by_gsim = rlzs_by_gsim
        self.ebruptures = ebruptures
        self.sitecol = sitecol
        self.imts = imts
        self.min_iml = min_iml
        self.truncation_level = truncation_level
        self.correlation_model = correlation_model
        self.samples = samples

    def init(self):
        """
        Initialize the computers. Should be called on the workers
        """
        self.N = len(self.sitecol.complete)
        self.I = len(self.imts)
        self.sids = self.sitecol.sids
        self.computers = []
        gsims = sorted(self.rlzs_by_gsim)
        for ebr in self.ebruptures:
            sites = site.FilteredSiteCollection(
                ebr.sids, self.sitecol.complete)
            computer = calc.gmf.GmfComputer(
                ebr, sites, self.imts, gsims,
                self.truncation_level, self.correlation_model)
            self.computers.append(computer)
        # dictionary rlzi -> array(imts, events, nbytes)
        self.gmdata = AccumDict(accum=numpy.zeros(len(self.imts) + 2, F32))
        self.eids = numpy.concatenate(
            [ebr.events['eid'] for ebr in self.ebruptures])
        # dictionary eid -> index
        self.eid2idx = dict(zip(self.eids, range(len(self.eids))))

    def gen_gmv(self, gsim):
        """
        Compute the GMFs for the given realization and populate the .gmdata
        array. Yields tuples of the form (sid, eid, imti, gmv).
        """
        rlzs = self.rlzs_by_gsim[gsim]
        # short event IDs (48 bit) are enlarged to long event IDs (64 bit)
        # containing information about the realization index (16 bit);
        # the information is used in .get_hazard and compute_gmfs_and_curves
        for computer in self.computers:
            rup = computer.rupture
            sids = computer.sites.sids
            if self.samples > 1:
                all_eids = [get_array(rup.events, sample=rlz.sampleid)['eid']
                            for rlz in rlzs]
            else:
                all_eids = [rup.events['eid']] * len(rlzs)
            num_events = sum(len(eids) for eids in all_eids)
            # NB: the trick for performance is to keep the call to
            # compute.compute outside of the loop over the realizations
            # it is better to have few calls producing big arrays
            array = computer.compute(gsim, num_events)  # (i, n, e)
            n = 0
            for r, rlz in enumerate(rlzs):
                e = len(all_eids[r])
                gmdata = self.gmdata[rlz.ordinal]
                gmdata[EVENTS] += e
                for imti, imt in enumerate(self.imts):
                    min_gmv = self.min_iml[imti]
                    for i, eid in enumerate(all_eids[r]):
                        gmf = array[imti, :, n + i]
                        for sid, gmv in zip(sids, gmf):
                            if gmv > min_gmv:
                                gmdata[imti] += gmv
                                gmdata[NBYTES] += BYTES_PER_RECORD
                                yield r, sid, eid, imti, gmv
                n += e

    def get_hazard(self, gsim, data=None):
        """
        :param gsim: a GSIM instance
        :param data: if given, an iterator of records of dtype gmf_data_dt
        :returns: an array (rlzi, sid, imti) -> array(gmv, eid)
        """
        if data is None:
            data = self.gen_gmv(gsim)
        R = len(self.rlzs_by_gsim[gsim])
        gmfa = numpy.zeros((R, self.N, self.I), object)
        for rlzi, sid, eid, imti, gmv in data:
            lst = gmfa[rlzi, sid, imti]
            if lst == 0:
                gmfa[rlzi, sid, imti] = [(gmv, eid)]
            else:
                lst.append((gmv, eid))
        for idx, lst in numpy.ndenumerate(gmfa):
            gmfa[idx] = numpy.array(lst or [], gmv_eid_dt)
        return gmfa

gmv_eid_dt = numpy.dtype([('gmv', F32), ('eid', U64)])


class GmfDataGetter(GmfGetter):
    """
    Extracts a dictionary of GMVs from the datastore
    """
    def __init__(self, gmf_data, grp_id, rlzs_by_gsim, start=0, stop=None):
        self.gmf_data = gmf_data
        self.grp_id = grp_id
        self.rlzs_by_gsim = rlzs_by_gsim
        self.N = gmf_data.attrs['num_sites']  # used by get_hazard
        self.I = gmf_data.attrs['num_imts']  # used by get_hazard
        self.start = start
        self.stop = stop

    def init(self):
        pass

    def gen_gmv(self, gsim):
        """
        Yield gmv records from the datastore, if present
        """
        key = 'grp-%02d/%s' % (self.grp_id, gsim)
        try:
            dset = self.gmf_data[key]
        except KeyError:
            return
        for rec in dset[self.start:self.stop]:
            yield rec

    @classmethod
    def gen_gmfs(cls, gmf_data, rlzs_assoc, eid=None):
        """
        Yield GMF records
        """
        if eid is not None:  # extract the grp_id from the eid
            grp_ids = [eid // TWO48]
        else:
            grp_ids = rlzs_assoc.gsims_by_grp_id
        for grp_id in grp_ids:
            rlzs_by_gsim = rlzs_assoc.get_rlzs_by_gsim(grp_id)
            getter = cls(gmf_data, grp_id, rlzs_by_gsim)
            for gsim, rlzs in rlzs_by_gsim.items():
                for rec in getter.gen_gmv(gsim):
                    if eid is None or eid == rec['eid']:
                        rec['rlzi'] = rlzs[rec['rlzi']].ordinal
                        yield rec


def get_rlzs(riskinput):
    """
    Returns the realizations contained in the riskinput object.
    """
    all_rlzs = []
    for gsim, rlzs in sorted(riskinput.hazard_getter.rlzs_by_gsim.items()):
        all_rlzs.extend(rlzs)
    return all_rlzs


class RiskInput(object):
    """
    Contains all the assets and hazard values associated to a given
    imt and site.

    :param hazard_getter:
        a callable returning the hazard data for a given realization
    :param assets_by_site:
        array of assets, one per site
    :param eps_dict:
        dictionary of epsilons
    """
    def __init__(self, hazard_getter, assets_by_site, eps_dict):
        self.hazard_getter = hazard_getter
        self.assets_by_site = assets_by_site
        self.eps = eps_dict
        taxonomies_set = set()
        aids = []
        for assets in self.assets_by_site:
            for asset in assets:
                taxonomies_set.add(asset.taxonomy)
                aids.append(asset.ordinal)
        self.aids = numpy.array(aids, numpy.uint32)
        self.taxonomies = sorted(taxonomies_set)
        self.weight = len(self.aids)

    rlzs = property(get_rlzs)

    @property
    def imt_taxonomies(self):
        """Return a list of pairs (imt, taxonomies) with a single element"""
        return [(self.imt, self.taxonomies)]

    def epsilon_getter(self, asset_ordinals):
        """
        :param asset_ordinals: list of ordinals of the assets
        :returns: a closure returning an array of epsilons from the event IDs
        """
        return lambda dummy1, dummy2: (
            [self.eps[aid] for aid in asset_ordinals]
            if self.eps else None)

    def __repr__(self):
        return '<%s taxonomy=%s, %d asset(s)>' % (
            self.__class__.__name__, ', '.join(self.taxonomies), self.weight)


class RiskInputFromRuptures(object):
    """
    Contains all the assets associated to the given IMT and a subsets of
    the ruptures for a given calculation.

    :param hazard_getter:
        a callable returning the hazard data for a given realization
    :params epsilons:
        a matrix of epsilons (or None)
    """
    def __init__(self, hazard_getter, epsilons=None):
        self.hazard_getter = hazard_getter
        self.weight = sum(sr.weight for sr in hazard_getter.ebruptures)
        if epsilons is not None:
            self.eps = epsilons  # matrix N x E, events in this block

    rlzs = property(get_rlzs)

    def epsilon_getter(self, asset_ordinals):
        """
        :param asset_ordinals: ordinals of the assets
        :returns: a closure returning an array of epsilons from the event IDs
        """
        if not hasattr(self, 'eps'):
            return lambda aid, eids: None

        def geteps(aid, eids):
            idxs = [self.hazard_getter.eid2idx[eid] for eid in eids]
            return self.eps[aid, idxs]
        return geteps

    def __repr__(self):
        return '<%s imts=%s, weight=%d>' % (
            self.__class__.__name__, self.hazard_getter.imts, self.weight)


def make_eps(assetcol, num_samples, seed, correlation):
    """
    :param assetcol: an AssetCollection instance
    :param int num_samples: the number of ruptures
    :param int seed: a random seed
    :param float correlation: the correlation coefficient
    :returns: epsilons matrix of shape (num_assets, num_samples)
    """
    assets_by_taxo = groupby(assetcol, by_taxonomy)
    eps = numpy.zeros((len(assetcol), num_samples), numpy.float32)
    for taxonomy, assets in assets_by_taxo.items():
        # the association with the epsilons is done in order
        assets.sort(key=operator.attrgetter('idx'))
        shape = (len(assets), num_samples)
        logging.info('Building %s epsilons for taxonomy %s', shape, taxonomy)
        zeros = numpy.zeros(shape)
        epsilons = scientific.make_epsilons(zeros, seed, correlation)
        for asset, epsrow in zip(assets, epsilons):
            eps[asset.ordinal] = epsrow
    return eps


def str2rsi(key):
    """
    Convert a string of the form 'rlz-XXXX/sid-YYYY/ZZZ'
    into a triple (XXXX, YYYY, ZZZ)
    """
    rlzi, sid, imt = key.split('/')
    return int(rlzi[4:]), int(sid[4:]), imt


def rsi2str(rlzi, sid, imt):
    """
    Convert a triple (XXXX, YYYY, ZZZ) into a string of the form
    'rlz-XXXX/sid-YYYY/ZZZ'
    """
    return 'rlz-%04d/sid-%04d/%s' % (rlzi, sid, imt)


class LossRatiosGetter(object):
    """
    Read loss ratios from the datastore for all realizations or for a specific
    realization.

    :param dstore: a DataStore instance
    """
    def __init__(self, dstore):
        self.dstore = dstore

    # used in the loss curves exporter
    def get(self, aids, rlzi):
        """
        :param aids: a list of A asset ordinals
        :param rlzi: a realization ordinal
        :returns: a dictionary aid -> list of loss ratios
        """
        data = self.dstore['all_loss_ratios/data']
        indices = self.dstore['all_loss_ratios/indices'][aids]  # (A, T, 2)
        dic = collections.defaultdict(list)  # aid -> ratios
        for aid, idxs in zip(aids, indices):
            for idx in idxs:
                for rec in data[idx[0]: idx[1]]:
                    if rlzi == rec['rlzi']:
                        dic[aid].append(rec['ratios'])
        return dic

    # used in the calculator
    def get_all(self, aids):
        """
        :param aids: a list of A asset ordinals
        :returns: a list of A composite arrays of dtype `lrs_dt`
        """
        data = self.dstore['all_loss_ratios/data']
        indices = self.dstore['all_loss_ratios/indices'][aids]  # (A, T, 2)
        loss_ratio_data = []
        for aid, idxs in zip(aids, indices):
            arr = numpy.concatenate([data[idx[0]: idx[1]] for idx in idxs])
            loss_ratio_data.append(arr)
        return loss_ratio_data
