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
from openquake.baselib.python3compat import zip, encode, decode
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

FIELDS = ('site_id', 'lon', 'lat', 'idx', 'area', 'number',
          'occupants', 'deductible-', 'insurance_limit-', 'retrofitted-')

by_taxonomy = operator.attrgetter('taxonomy')

aids_dt = numpy.dtype([('aids', hdf5.vuint32)])


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

    def __init__(self, assets_by_site, assets_by_tag, cost_calculator,
                 time_event, time_events=''):
        self.cc = cost_calculator
        self.time_event = time_event
        self.time_events = time_events
        self.tot_sites = len(assets_by_site)
        self.array = self.build_asset_collection(assets_by_site, time_event)
        dic = dict(zip(self.array['idx'], range(len(self.array))))
        self.tagnames = assets_by_tag.tagnames
        self.aids_by_tag = {}
        for tag, idxs in assets_by_tag.items():
            aids = []
            for idx in idxs:
                try:
                    aids.append(dic[idx])
                except KeyError:  # discarded by assoc_assets_sites
                    continue
            self.aids_by_tag[tag] = set(aids)
        fields = self.array.dtype.names
        self.loss_types = [f[6:] for f in fields if f.startswith('value-')]
        if 'occupants' in fields:
            self.loss_types.append('occupants')
        self.loss_types.sort()
        self.deduc = [n for n in fields if n.startswith('deductible-')]
        self.i_lim = [n for n in fields if n.startswith('insurance_limit-')]
        self.retro = [n for n in fields if n.startswith('retrofitted-')]

    @property
    def taxonomies(self):
        """
        Return a list of taxonomies, one per asset (with duplicates)
        """
        if not hasattr(self, '_taxonomy'):
            self._taxonomy = [None] * len(self)
            for tag, aids in self.aids_by_tag.items():
                name, value = tag.split('=', 1)
                if name == 'taxonomy':
                    for aid in aids:
                        self._taxonomy[aid] = value
        return self._taxonomy

    def tags(self):
        """
        :returns: list of sorted tags
        """
        return sorted(self.aids_by_tag)

    def units(self, loss_types):
        """
        :param: a list of loss types
        :returns: an array of units as byte strings, suitable for HDF5
        """
        units = self.cc.units
        lst = []
        for lt in loss_types:
            if lt.endswith('_ins'):
                lt = lt[:-4]
            lst.append(encode(units[lt]))
        return numpy.array(lst)

    def assets_by_site(self):
        """
        :returns: numpy array of lists with the assets by each site
        """
        assets_by_site = [[] for sid in range(self.tot_sites)]
        for i, ass in enumerate(self.array):
            assets_by_site[ass['site_id']].append(self[i])
        return numpy.array(assets_by_site)

    def values(self, aids=None):
        """
        :param aids: asset indices where to compute the values (None means all)
        :returns: a structured array of asset values by loss type
        """
        if aids is None:
            aids = range(len(self))
        loss_dt = numpy.dtype([(str(lt), F32) for lt in self.loss_types])
        vals = numpy.zeros(len(aids), loss_dt)  # asset values by loss_type
        for i, aid in enumerate(aids):
            asset = self[aid]
            for lt in self.loss_types:
                vals[i][lt] = asset.value(lt, self.time_event)
        return vals

    def tagmask(self):
        """
        :returns: array of booleans of shape (A, T)
        """
        tags = self.tags()
        tagidx = {t: i for i, t in enumerate(tags)}
        mask = numpy.zeros((len(self), len(tags)), bool)
        for tag, aids in self.aids_by_tag.items():
            mask[sorted(aids), tagidx[tag]] = True
        return mask

    def get_tax_idx(self):
        """
        :returns: list of tag indices corresponding to taxonomies
        """
        return [i for i, t in enumerate(self.tags())
                if t.startswith('taxonomy=')]

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __getitem__(self, aid):
        a = self.array[aid]
        values = {lt: a['value-' + lt] for lt in self.loss_types
                  if lt != 'occupants'}
        if 'occupants' in self.array.dtype.names:
            values['occupants_' + str(self.time_event)] = a['occupants']
        return riskmodels.Asset(
                a['idx'],
                self.taxonomies[aid],
                number=a['number'],
                location=(valid.longitude(a['lon']),  # round coordinates
                          valid.latitude(a['lat'])),
                values=values,
                area=a['area'],
                deductibles={lt[self.D:]: a[lt] for lt in self.deduc},
                insurance_limits={lt[self.I:]: a[lt] for lt in self.i_lim},
                retrofitteds={lt[self.R:]: a[lt] for lt in self.retro},
                calc=self.cc, ordinal=aid)

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
                 'tagnames': encode(self.tagnames),
                 'nbytes': self.array.nbytes}
        tags, all_aids = [], []
        for tag, aids in sorted(self.aids_by_tag.items()):
            tags.append(tag)
            all_aids.append((numpy.array(sorted(aids), U32),))
        return dict(array=self.array,
                    tags=numpy.array(tags, hdf5.vstr),
                    aids=numpy.array(all_aids, aids_dt),
                    cost_calculator=self.cc), attrs

    def __fromh5__(self, dic, attrs):
        for name in ('time_events', 'loss_types', 'deduc', 'i_lim', 'retro'):
            setattr(self, name, attrs[name].split())
        self.tagnames = attrs['tagnames']
        self.time_event = attrs['time_event']
        self.tot_sites = attrs['tot_sites']
        self.nbytes = attrs['nbytes']
        self.array = dic['array'].value
        self.cc = dic['cost_calculator']
        # dic['aids'] is an array of dtype `aids_dt` with field 'aids'
        self.aids_by_tag = {
            tag: set(aids) for tag, aids in zip(
                dic['tags'], dic['aids']['aids'])}

    @staticmethod
    def build_asset_collection(assets_by_site, time_event=None):
        """
        :param assets_by_site: a list of lists of assets
        :param time_event: a time event string (or None)
        :returns: an array `assetcol`
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
        for candidate in sorted(candidate_loss_types):
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
        asset_dt = numpy.dtype(
            [('idx', U32), ('lon', F32), ('lat', F32), ('site_id', U32),
             ('number', F32), ('area', F32)] + [
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
                    if field == 'number':
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
        return assetcol


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
                if 'exposure' not in oqparam.inputs:
                    raise RuntimeError(
                        'There are risk files in %r but not '
                        'an exposure' % oqparam.inputs['job_ini'])
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
        self.curve_params = self.make_curve_params(oqparam)
        self.loss_types = [cp.loss_type for cp in self.curve_params]
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

    def make_curve_params(self, oqparam):
        # NB: populate the inner lists .loss_types too
        cps = []
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
                if len(curve_resolutions) > 1:  # example in test_case_5
                    logging.info(
                        'Different num_loss_ratios:\n%s', '\n'.join(lines))
                cp = scientific.CurveParams(
                    l, loss_type, max(curve_resolutions), ratios, True)
            else:  # event_based or scenario calculators
                cp = scientific.CurveParams(
                    l, loss_type, oqparam.loss_curve_resolution,
                    default_loss_ratios, False)
            cps.append(cp)
            self.lti[loss_type] = l
        return cps

    def get_loss_ratios(self):
        """
        :returns: a 1-dimensional composite array with loss ratios by loss type
        """
        lst = [('user_provided', numpy.bool)]
        for cp in self.curve_params:
            lst.append((cp.loss_type, F32, len(cp.ratios)))
        loss_ratios = numpy.zeros(1, numpy.dtype(lst))
        for cp in self.curve_params:
            loss_ratios['user_provided'] = cp.user_provided
            loss_ratios[cp.loss_type] = tuple(cp.ratios)
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
        dic = collections.defaultdict(list)
        for sid, assets in enumerate(assets_by_site):
            group = groupby(assets, by_taxonomy)
            for taxonomy in group:
                epsgetter = riskinput.epsilon_getter
                dic[taxonomy].append((sid, group[taxonomy], epsgetter))
        imti = {imt: i for i, imt in enumerate(hazard_getter.imts)}
        if hasattr(hazard_getter, 'rlzs_by_gsim'):
            # save memory in event based risk by working one gsim at the time
            for gsim in hazard_getter.rlzs_by_gsim:
                with mon_hazard:
                    hazard = hazard_getter.get_hazard(gsim)
                with mon_risk:
                    for out in self._gen_outputs(
                            hazard, imti, dic, hazard_getter.eids):
                        yield out
        else:
            with mon_hazard:
                hazard = hazard_getter.get_hazard()
            with mon_risk:
                for out in self._gen_outputs(
                        hazard, imti, dic, hazard_getter.eids):
                    yield out

        if hasattr(hazard_getter, 'gmdata'):  # for event based risk
            riskinput.gmdata = hazard_getter.gmdata

    def _gen_outputs(self, hazard, imti, dic, eids):
        for taxonomy in sorted(dic):
            riskmodel = self[taxonomy]
            rangeI = [imti[riskmodel.risk_functions[lt].imt]
                      for lt in self.loss_types]
            for rlzi, hazardr in sorted(hazard.items()):
                for sid, assets, epsgetter in dic[taxonomy]:
                    try:
                        haz = hazardr[sid]
                    except KeyError:  # no hazard for this site
                        continue
                    if len(haz) == 0:  # no hazard for this site
                        continue
                    elif isinstance(haz, numpy.ndarray):  # event_based
                        eids = haz['eid']
                        gmvs = haz['gmv']
                        data = {i: (gmvs[:, i], eids) for i in rangeI}
                    elif eids is not None:  # gmf_ebrisk
                        data = {i: (haz[i], eids) for i in rangeI}
                    else:  # classical or scenario from gmfs
                        data = haz
                    out = [None] * len(self.lti)
                    for lti, i in enumerate(rangeI):
                        lt = self.loss_types[lti]
                        out[lti] = riskmodel(lt, assets, data[i], epsgetter)
                    yield Output(self.loss_types, assets, out, sid, rlzi)

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
        an array of curves of shape (R, N) or a GMF array of shape (R, N, E, I)
    :param imts:
        a list of IMT strings
    :param eids:
        an array of event IDs (or None)
    """
    def __init__(self, kind, hazards_by_rlz, imts, eids=None):
        assert kind in ('poe', 'gmf'), kind
        self.kind = kind
        self.imts = imts
        self.eids = eids
        self.data = collections.OrderedDict()
        self.num_rlzs = len(hazards_by_rlz)
        for rlzi, hazard in enumerate(hazards_by_rlz):
            self.data[rlzi] = datadict = {}
            for idx, haz in enumerate(hazards_by_rlz[rlzi]):
                datadict[idx] = lst = [None for imt in imts]
                for imti, imt in enumerate(self.imts):
                    if kind == 'poe':
                        lst[imti] = haz[imt]  # imls
                    else:  # gmf
                        lst[imti] = haz[:, imti]

        if kind == 'gmf':
            # now some attributes set for API compatibility with the GmfGetter
            # number of ground motion fields
            # dictionary rlzi -> array(imts, events, nbytes)
            self.gmdata = AccumDict(accum=numpy.zeros(len(self.imts) + 2, F32))

    def init(self):  # for API compatibility
        pass

    def get_hazard(self):
        """
        :param gsim: a GSIM instance
        :returns: an OrderedDict rlzi -> datadict
        """
        if self.kind == 'gmf':
            # save info useful for debugging into gmdata
            I = len(self.imts)
            for rlzi, datadict in self.data.items():
                arr = numpy.zeros(I + 2, F32)  # imt, events, bytes
                arr[-1] = 4 * I * len(datadict)  # nbytes
                for lst in datadict.values():
                    for i, gmvs in enumerate(lst):
                        arr[i] += gmvs.sum()
                self.gmdata[rlzi] += arr
        return self.data


class GmfGetter(object):
    """
    An hazard getter with methods .gen_gmv and .get_hazard returning
    ground motion values.
    """
    kind = 'gmf'

    def __init__(self, rlzs_by_gsim, ebruptures, sitecol, imts,
                 min_iml, truncation_level, correlation_model, samples):
        assert sitecol is sitecol.complete, sitecol
        self.grp_id = ebruptures[0].grp_id
        self.rlzs_by_gsim = rlzs_by_gsim
        self.num_rlzs = sum(len(rlzs) for gsim, rlzs in rlzs_by_gsim.items())
        self.ebruptures = ebruptures
        self.sitecol = sitecol
        self.imts = imts
        self.min_iml = min_iml
        self.truncation_level = truncation_level
        self.correlation_model = correlation_model
        self.samples = samples
        self.gmf_data_dt = numpy.dtype(
            [('rlzi', U16), ('sid', U32),
             ('eid', U64), ('gmv', (F32, (len(imts),)))])

    def init(self):
        """
        Initialize the computers. Should be called on the workers
        """
        self.N = len(self.sitecol.complete)
        self.I = I = len(self.imts)
        self.R = sum(len(rlzs) for rlzs in self.rlzs_by_gsim.values())
        self.gmv_dt = numpy.dtype(
            [('sid', U32), ('eid', U64), ('gmv', (F32, (I,)))])
        self.gmv_eid_dt = numpy.dtype([('gmv', (F32, (I,))), ('eid', U64)])
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

    def gen_gmv(self, gsim=None):
        """
        Compute the GMFs for the given realization and populate the .gmdata
        array. Yields tuples of the form (sid, eid, imti, gmv).
        """
        itemsize = self.gmf_data_dt.itemsize
        sample = 0  # in case of sampling the realizations have a corresponding
        # sample number from 0 to the number of samples of the given src model
        gsims = self.rlzs_by_gsim if gsim is None else [gsim]
        for gsim in gsims:  # OrderedDict
            rlzs = self.rlzs_by_gsim[gsim]
            for computer in self.computers:
                rup = computer.rupture
                sids = computer.sites.sids
                if self.samples > 1:
                    # events of the current slice of realizations
                    all_eids = [get_array(rup.events, sample=s)['eid']
                                for s in range(sample, sample + len(rlzs))]
                else:
                    all_eids = [rup.events['eid']] * len(rlzs)
                num_events = sum(len(eids) for eids in all_eids)
                # NB: the trick for performance is to keep the call to
                # compute.compute outside of the loop over the realizations
                # it is better to have few calls producing big arrays
                array = computer.compute(gsim, num_events).transpose(1, 0, 2)
                # shape (N, I, E)
                for i, miniml in enumerate(self.min_iml):  # gmv < minimum
                    arr = array[:, i, :]
                    arr[arr < miniml] = 0
                n = 0
                for r, rlzi in enumerate(rlzs):
                    e = len(all_eids[r])
                    gmdata = self.gmdata[rlzi]
                    gmdata[EVENTS] += e
                    for ei, eid in enumerate(all_eids[r]):
                        gmf = array[:, :, n + ei]  # shape (N, I)
                        tot = gmf.sum(axis=0)  # shape (I,)
                        if not tot.sum():
                            continue
                        for i, val in enumerate(tot):
                            gmdata[i] += val
                        for sid, gmv in zip(sids, gmf):
                            if gmv.sum():
                                gmdata[NBYTES] += itemsize
                                yield rlzi, sid, eid, gmv
                    n += e
            sample += len(rlzs)

    def get_hazard(self, gsim=None, data=None):
        """
        :param data: if given, an iterator of records of dtype gmf_data_dt
        :returns: an array (rlzi, sid, imti) -> array(gmv, eid)
        """
        if data is None:
            data = self.gen_gmv(gsim)
        hazard = collections.defaultdict(lambda: collections.defaultdict(list))
        for rlzi, sid, eid, gmv in data:
            hazard[rlzi][sid].append((gmv, eid))
        for haz in hazard.values():
            for sid in haz:
                haz[sid] = numpy.array(haz[sid], self.gmv_eid_dt)
        return hazard


class GmfDataGetter(GmfGetter):
    """
    Extracts a dictionary of GMVs from the datastore
    """
    def __init__(self, gmf_data, start=0, stop=None):
        self.gmf_data = gmf_data
        self.start = start
        self.stop = stop

    def init(self):
        pass

    def gen_gmv(self):
        """
        Returns gmv records from the datastore, if any
        """
        return self.gmf_data['data'][self.start:self.stop]

    @classmethod
    def gen_gmfs(cls, gmf_data, eid=None):
        """
        Returns a gmf_data_dt array
        """
        data = cls(gmf_data).gen_gmv()
        if eid is None:
            return data
        return data[data['eid'] == eid]


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

    @property
    def imt_taxonomies(self):
        """Return a list of pairs (imt, taxonomies) with a single element"""
        return [(self.imt, self.taxonomies)]

    def epsilon_getter(self, aid, eids):
        """
        :param aid: asset ordinal
        :param eids: ignored
        :returns: an array of E epsilons
        """
        if not self.eps:
            return
        eps = self.eps[aid]
        if isinstance(eps, numpy.ndarray):
            return eps
        # else assume it is zero
        return numpy.zeros(len(eids), F32)

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

    def epsilon_getter(self, aid, eids):
        """
        :param aid: asset ordinal
        :param eids: E event IDs
        :returns: an array of E epsilons
        """
        if not hasattr(self, 'eps'):
            return None
        idxs = [self.hazard_getter.eid2idx[eid] for eid in eids]
        return self.eps[aid, idxs]

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
    def __init__(self, dstore, aids=None, lazy=True):
        self.dstore = dstore
        dset = self.dstore['all_loss_ratios/indices']
        self.aids = list(aids or range(len(dset)))
        self.indices = [dset[aid] for aid in self.aids]
        self.data = None if lazy else self.get_all()

    # used in the loss curves exporter
    def get(self, rlzi):
        """
        :param rlzi: a realization ordinal
        :returns: a dictionary aid -> array of shape (E, LI)
        """
        data = self.dstore['all_loss_ratios/data']
        dic = collections.defaultdict(list)  # aid -> ratios
        for aid, idxs in zip(self.aids, self.indices):
            for idx in idxs:
                for rec in data[idx[0]: idx[1]]:  # dtype (rlzi, ratios)
                    if rlzi == rec['rlzi']:
                        dic[aid].append(rec['ratios'])
        return {a: numpy.array(dic[a]) for a in dic}

    # used in the calculator
    def get_all(self):
        """
        :returns: a list of A composite arrays of dtype `lrs_dt`
        """
        if getattr(self, 'data', None) is not None:
            return self.data
        self.dstore.open()  # if closed
        data = self.dstore['all_loss_ratios/data']
        loss_ratio_data = []
        for aid, idxs in zip(self.aids, self.indices):
            if len(idxs):
                arr = numpy.concatenate([data[idx[0]: idx[1]] for idx in idxs])
            else:
                # FIXME: a test for this case is missing
                arr = numpy.array([], data.dtype)
            loss_ratio_data.append(arr)
        return loss_ratio_data
