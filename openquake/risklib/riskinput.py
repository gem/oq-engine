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

from openquake.baselib import hdf5, performance
from openquake.baselib.general import (
    groupby, group_array, get_array, AccumDict)
from openquake.hazardlib import site, calc
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
indices_dt = numpy.dtype([('start', U32), ('stop', U32)])


def get_refs(assets, hdf5path):
    """
    Debugging method returning the string IDs of the assets from the datastore
    """
    with hdf5.File(hdf5path, 'r') as f:
        return f['asset_refs'][[a.idx for a in assets]]


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
                    zip(sorted(rmdict.items()), sorted(retrodict.items())):
                assert taxonomy == taxonomy_  # same taxonomies
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
        # the CurveParams are used only in classical_risk, classical_bcr
        # NB: populate the inner lists .loss_types too
        cps = []
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
            else:  # used only to store the association l -> loss_type
                cp = scientific.CurveParams(l, loss_type, 0, [], False)
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

    def gen_outputs(self, riskinput, monitor=performance.Monitor(),
                    assetcol=None):
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
        sids = hazard_getter.sids
        with mon_context:
            if assetcol is None:  # scenario, classical
                assets_by_site = riskinput.assets_by_site
            else:
                assets_by_site = assetcol.assets_by_site()
        # group the assets by taxonomy
        dic = collections.defaultdict(list)
        for sid, assets in zip(sids, assets_by_site):
            group = groupby(assets, by_taxonomy)
            for taxonomy in group:
                epsgetter = riskinput.epsilon_getter
                dic[taxonomy].append((sid, group[taxonomy], epsgetter))
        imti = {imt: i for i, imt in enumerate(hazard_getter.imtls)}
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
            rangeM = [imti[riskmodel.risk_functions[lt].imt]
                      for lt in self.loss_types]
            for sid, assets, epsgetter in dic[taxonomy]:
                try:
                    haz_by_sid = hazard[sid]
                except KeyError:  # no hazard for this site
                    continue
                for rlzi, haz in sorted(haz_by_sid.items()):
                    if isinstance(haz, numpy.ndarray):
                        # event based and scenario
                        eids = haz['eid']
                        data = {i: (haz['gmv'][:, i], eids)
                                for i in rangeM}
                    elif eids is not None:  # gmf_ebrisk
                        data = {i: (haz[i], eids) for i in rangeM}
                    else:  # classical
                        data = haz
                    data_by_lt = [data[imti[riskmodel.risk_functions[lt].imt]]
                                  for lt in self.loss_types]
                    out = riskmodel.get_output(assets, data_by_lt, epsgetter)
                    out.loss_types = self.loss_types
                    out.assets = assets
                    out.sid = sid
                    out.rlzi = rlzi
                    out.eids = eids
                    yield out

    def __toh5__(self):
        loss_types = hdf5.array_of_vstr(self._get_loss_types())
        return self._riskmodels, dict(covs=self.covs, loss_types=loss_types)

    def __repr__(self):
        lines = ['%s: %s' % item for item in sorted(self.items())]
        return '<%s(%d, %d)\n%s>' % (
            self.__class__.__name__, len(lines), self.covs, '\n'.join(lines))


class GmfDataGetter(collections.Mapping):
    """
    A dictionary-like object {sid: dictionary by realization index}
    """
    def __init__(self, dstore, sids):
        self.dstore = dstore
        self.sids = sids

    def __getitem__(self, sid):
        dset = self.dstore['gmf_data/data']
        idxs = self.dstore['gmf_data/indices'][sid]
        array = numpy.concatenate([dset[start:stop] for start, stop in idxs])
        return group_array(array, 'rlzi')

    def __iter__(self):
        return iter(self.sids)

    def __len__(self):
        return len(self.sids)


class HazardGetter(object):
    """
    :param dstore:
        DataStore instance
    :param kind:
        kind of HazardGetter; can be 'poe' or 'gmf'
    :param sids:
        hazard site IDs
    :param imtls:
        intensity measure types and levels object
    :param eids:
        an array of event IDs (or None)
    """
    def __init__(self, dstore, kind, getter, imtls, eids=None):
        assert kind in ('poe', 'gmf'), kind
        self.kind = kind
        self.sids = getter.sids
        self._getter = getter
        self.imtls = imtls
        self.eids = eids
        self.num_rlzs = dstore['csm_info'].get_num_rlzs()
        oq = dstore['oqparam']
        self.E = getattr(oq, 'number_of_ground_motion_fields', None)
        self.I = len(oq.imtls)
        if kind == 'gmf':
            # now some attributes set for API compatibility with the GmfGetter
            # number of ground motion fields
            # dictionary rlzi -> array(imts, events, nbytes)
            self.gmdata = AccumDict(
                accum=numpy.zeros(len(self.imtls) + 2, F32))

    def init(self):
        if hasattr(self, 'data'):  # alreay initialized
            return
        self.data = collections.OrderedDict()
        if self.kind == 'poe':
            hcurves = self._getter.get_hcurves(self.imtls)  # shape (R, N)
            for sid, hcurve_by_rlz in zip(self.sids, hcurves.T):
                self.data[sid] = datadict = {}
                for rlzi, hcurve in enumerate(hcurve_by_rlz):
                    datadict[rlzi] = lst = [None for imt in self.imtls]
                    for imti, imt in enumerate(self.imtls):
                        lst[imti] = hcurve[imt]  # imls
        else:  # gmf
            for sid in self.sids:
                self.data[sid] = data = self._getter[sid]
                if not data:  # no GMVs, return 0, counted in no_damage
                    self.data[sid] = {
                        rlzi: numpy.zeros((self.E, self.I),
                                          [('gmv', F32), ('eid', U64)])
                        for rlzi in range(self.num_rlzs)}

    def get_hazard(self):
        """
        :param gsim: a GSIM instance
        :returns: an OrderedDict rlzi -> datadict
        """
        return self.data


class GmfGetter(object):
    """
    An hazard getter with methods .gen_gmv and .get_hazard returning
    ground motion values.
    """
    kind = 'gmf'

    def __init__(self, rlzs_by_gsim, ebruptures, sitecol, imtls,
                 min_iml, truncation_level, correlation_model, samples=1):
        assert sitecol is sitecol.complete, sitecol
        self.grp_id = ebruptures[0].grp_id
        self.rlzs_by_gsim = rlzs_by_gsim
        self.num_rlzs = sum(len(rlzs) for gsim, rlzs in rlzs_by_gsim.items())
        self.ebruptures = ebruptures
        self.sitecol = sitecol
        self.imtls = imtls
        self.min_iml = min_iml
        self.truncation_level = truncation_level
        self.correlation_model = correlation_model
        self.samples = samples
        self.gmf_data_dt = numpy.dtype(
            [('rlzi', U16), ('sid', U32),
             ('eid', U64), ('gmv', (F32, (len(imtls),)))])

    def init(self):
        """
        Initialize the computers. Should be called on the workers
        """
        self.N = len(self.sitecol.complete)
        self.I = I = len(self.imtls)
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
                ebr, sites, self.imtls, gsims,
                self.truncation_level, self.correlation_model)
            self.computers.append(computer)
        # dictionary rlzi -> array(imtls, events, nbytes)
        self.gmdata = AccumDict(accum=numpy.zeros(len(self.imtls) + 2, F32))
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
        hazard = numpy.array([collections.defaultdict(list)
                              for _ in range(self.N)])
        for rlzi, sid, eid, gmv in data:
            hazard[sid][rlzi].append((gmv, eid))
        for haz in hazard:
            for rlzi in haz:
                haz[rlzi] = numpy.array(haz[rlzi], self.gmv_eid_dt)
        return hazard


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
            self.__class__.__name__,
            list(self.hazard_getter.imtls),
            self.weight)


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
