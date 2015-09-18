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
# -*- coding: utf-8 -*-

import operator
import logging
import collections

import numpy

from openquake.baselib.general import groupby, split_in_blocks
from openquake.baselib.performance import DummyMonitor
from openquake.hazardlib.gsim.base import gsim_imt_dt
from openquake.risklib import scientific


def sorted_assets(assets_by_site):
    """
    :param assets_by_site: a list of lists of disjoint assets
    :returns: the assets sorted by .id
    """
    all_assets = []
    for assets in assets_by_site:
        all_assets.extend(assets)
    return sorted(all_assets, key=operator.attrgetter('id'))


def build_asset_collection(assets_by_site, time_event=None):
    """
    :param assets_by_site: a list of lists of assets
    :param time_event: a time event string (or None)
    :returns: an array with composite dtype
    """
    for assets in assets_by_site:
        if len(assets):
            first_asset = assets[0]
            break
    else:  # no break
        raise ValueError('There are no assets!')
    candidate_loss_types = list(first_asset.values)
    loss_types = []
    the_fatalities = 'fatalities_%s' % time_event
    for candidate in candidate_loss_types:
        if candidate.startswith('fatalities'):
            if candidate == the_fatalities:
                loss_types.append('fatalities')
            # discard fatalities for different time periods
        else:
            loss_types.append(candidate)
    deductible_d = first_asset.deductibles or {}
    limit_d = first_asset.insurance_limits or {}
    retrofitting_d = first_asset.retrofitting_values or {}
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
        [('asset_ref', '|S100'), ('site_id', numpy.uint32),
         ('taxonomy', numpy.uint32)] +
        [(name, float) for name in float_fields])
    num_assets = sum(len(assets) for assets in assets_by_site)
    assetcol = numpy.zeros(num_assets, asset_dt)
    asset_ordinal = 0
    fields = ['asset_ref', 'site_id'] + float_fields
    for sid, assets_ in enumerate(assets_by_site):
        for asset in sorted(assets_, key=operator.attrgetter('id')):
            asset.idx = asset_ordinal
            record = assetcol[asset_ordinal]
            asset_ordinal += 1
            for field in fields:
                if field == 'taxonomy':
                    value = sorted_taxonomies.index(asset.taxonomy)
                elif field == 'asset_ref':
                    value = asset.id
                elif field == 'site_id':
                    value = sid
                elif field == 'fatalities':
                    value = asset.values[the_fatalities]
                else:
                    try:
                        name, lt = field.split('~')
                    except ValueError:  # no ~ in field
                        name, lt = 'value', field
                    value = getattr(asset, name)(lt)
                record[field] = value
    return assetcol


class RiskModel(collections.Mapping):
    """
    A container (imt, taxonomy) -> workflow.

    :param workflows: a dictionary (imt, taxonomy) -> workflow
    :param damage_states: None or a list of damage states
    """
    def __init__(self, workflows, damage_states=None):
        self.damage_states = damage_states  # not None for damage calculations
        self._workflows = workflows
        self.loss_types = []
        self.curve_builders = []
        self.lti = {}  # loss_type -> idx
        self.covs = 0  # number of coefficients of variation

    def make_curve_builders(self, oqparam):
        """
        Populate the inner lists .loss_types, .curve_builders.
        """
        for i, loss_type in enumerate(self.get_loss_types()):
            if not oqparam.loss_ratios:
                loss_ratios = numpy.linspace(
                    0, 1, oqparam.loss_curve_resolution + 1)[1:]
                cb = scientific.CurveBuilder(loss_type, loss_ratios, False)
            else:  # user-provided loss ratios
                loss_ratios = oqparam.loss_ratios[loss_type]
                cb = scientific.CurveBuilder(loss_type, loss_ratios, True)
            self.curve_builders.append(cb)
            self.loss_types.append(loss_type)
            self.lti[loss_type] = i

    def get_loss_types(self):
        """
        :returns: a sorted list with all the loss_types contained in the model
        """
        ltypes = set()
        for wf in self.values():
            ltypes.update(wf.loss_types)
        return sorted(ltypes)

    def get_taxonomies(self, imt=None):
        """
        :returns: the set of taxonomies which are part of the RiskModel
        """
        if imt is None:
            return set(taxonomy for imt, taxonomy in self)
        return set(taxonomy for imt_str, taxonomy in self if imt_str == imt)

    def get_imts(self, taxonomy=None):
        if taxonomy is None:
            return set(imt for imt, taxonomy in self)
        return set(imt for imt, taxo in self if taxo == taxonomy)

    def get_imt_taxonomies(self):
        """
        For each IMT in the risk model, yield pairs (imt, taxonomies)
        with the taxonomies associated to the IMT. For fragility functions,
        there is a single taxonomy for each IMT.
        """
        by_imt = operator.itemgetter(0)
        by_taxo = operator.itemgetter(1)
        dic = groupby(self, by_imt, lambda group: list(map(by_taxo, group)))
        return list(dic.items())

    def __getitem__(self, imt_taxo):
        return self._workflows[imt_taxo]

    def __iter__(self):
        return iter(sorted(self._workflows))

    def __len__(self):
        return len(self._workflows)

    def build_input(self, imt, hazards_by_site, assets_by_site, eps_dict=None):
        """
        :param imt: an Intensity Measure Type
        :param hazards_by_site: an array of hazards per each site
        :param assets_by_site: an array of assets per each site
        :param eps_dict: a dictionary of epsilons per each asset
        :returns: a :class:`RiskInput` instance
        """
        imt_taxonomies = [(imt, self.get_taxonomies(imt))]
        return RiskInput(imt_taxonomies, hazards_by_site,
                         assets_by_site, eps_dict)

    def build_inputs_from_ruptures(self, sitecol, all_ruptures,
                                   gsims_by_col, trunc_level, correl_model,
                                   eps_dict, hint):
        """
        :param sitecol: a SiteCollection instance
        :param all_ruptures: the complete list of SESRupture instances
        :param gsims_by_col: a dictionary of GSIM instances
        :param trunc_level: the truncation level (or None)
        :param correl_model: the correlation model (or None)
        :param eps_dict: a dictionary asset_ref -> epsilon array
        :param hint: hint for how many blocks to generate

        Yield :class:`RiskInputFromRuptures` instances.
        """
        imt_taxonomies = list(self.get_imt_taxonomies())
        by_col = operator.attrgetter('col_id')
        rup_start = rup_stop = 0
        num_epsilons = len(eps_dict[next(iter(eps_dict))])
        for ses_ruptures in split_in_blocks(
                all_ruptures, hint or 1, key=by_col):
            rup_stop += len(ses_ruptures)
            gsims = gsims_by_col[ses_ruptures[0].col_id]
            yield RiskInputFromRuptures(
                imt_taxonomies, sitecol, ses_ruptures,
                gsims, trunc_level, correl_model, num_epsilons,
                slice(rup_start, rup_stop))
            rup_start = rup_stop

    def gen_outputs(self, riskinputs, rlzs_assoc, monitor):
        """
        Group the assets per taxonomy and compute the outputs by using the
        underlying workflows. Yield the outputs generated as dictionaries
        out_by_rlz.

        :param riskinputs: a list of riskinputs with consistent IMT
        :param rlzs_assoc: a RlzsAssoc instance
        :param monitor: a monitor object used to measure the performance
        """
        mon_hazard = monitor('getting hazard', autoflush=False)
        mon_risk = monitor('computing individual risk', autoflush=False)
        for riskinput in riskinputs:
            try:
                assets_by_site = riskinput.assets_by_site
            except AttributeError:  # for event_based_risk
                assets_by_site = monitor.assets_by_site
            try:
                eps_dict = monitor.eps_dict
            except AttributeError:
                eps_dict = {}
            with mon_hazard:
                # get assets, hazards, epsilons
                a, h, e = riskinput.get_all(
                    rlzs_assoc, assets_by_site, eps_dict)
            with mon_risk:
                # compute the outputs by using the worklow
                for imt, taxonomies in riskinput.imt_taxonomies:
                    for taxonomy in taxonomies:
                        assets, hazards, epsilons = [], [], []
                        for asset, hazard, epsilon in zip(a, h, e):
                            if asset.taxonomy == taxonomy:
                                assets.append(asset)
                                hazards.append(hazard[imt])
                                epsilons.append(epsilon)
                        if not assets:
                            continue
                        workflow = self[imt, taxonomy]
                        for out_by_rlz in workflow.gen_out_by_rlz(
                                assets, hazards, epsilons, riskinput.tags):
                            # this is ugly, but we must cope with that
                            if hasattr(riskinput, 'rup_slice'):
                                out_by_rlz.rup_slice = riskinput.rup_slice
                            yield out_by_rlz
        mon_hazard.flush()
        mon_risk.flush()

    def __repr__(self):
        lines = ['%s: %s' % item for item in sorted(self.items())]
        return '<%s(%d, %d)\n%s>' % (
            self.__class__.__name__, len(lines), self.covs, '\n'.join(lines))


class RiskInput(object):
    """
    Contains all the assets and hazard values associated to a given
    imt and site.

    :param imt: Intensity Measure Type string
    :param hazard_assets_by_taxo: pairs (hazard, {imt: assets}) for each site
    """
    def __init__(self, imt_taxonomies, hazard_by_site, assets_by_site,
                 eps_dict=None):
        [(self.imt, taxonomies)] = imt_taxonomies
        self.hazard_by_site = hazard_by_site
        self.assets_by_site = [
            [a for a in assets if a.taxonomy in taxonomies]
            for assets in assets_by_site]
        taxonomies = set()
        self.weight = 0
        for assets in self.assets_by_site:
            for asset in assets:
                taxonomies.add(asset.taxonomy)
            self.weight += len(assets)
        self.taxonomies = sorted(taxonomies)
        self.tags = None  # for API compatibility with RiskInputFromRuptures
        self.eps_dict = eps_dict or {}

    @property
    def imt_taxonomies(self):
        """Return a list of pairs (imt, taxonomies) with a single element"""
        return [(self.imt, self.taxonomies)]

    def get_all(self, rlzs_assoc, assets_by_site=None, eps_dict=None):
        """
        :returns:
            lists of assets, hazards and epsilons
        """
        assets, hazards, epsilons = [], [], []
        if assets_by_site is None:
            assets_by_site = self.assets_by_site
        for hazard, assets_ in zip(self.hazard_by_site, assets_by_site):
            for asset in assets_:
                assets.append(asset)
                hazards.append({self.imt: rlzs_assoc.combine(hazard)})
                epsilons.append(self.eps_dict.get(asset.id, None))
        return assets, hazards, epsilons

    def __repr__(self):
        return '<%s IMT=%s, taxonomy=%s, weight=%d>' % (
            self.__class__.__name__, self.imt, ', '.join(self.taxonomies),
            self.weight)


def make_eps_dict(assets_by_site, num_samples, seed, correlation):
    """
    :param assets_by_site: a list of lists of assets
    :param int num_samples: the number of ruptures
    :param int seed: a random seed
    :param float correlation: the correlation coefficient
    :returns: dictionary asset_id -> epsilons
    """
    eps_dict = {}  # asset_id -> epsilons
    all_assets = (a for assets in assets_by_site for a in assets)
    assets_by_taxo = groupby(all_assets, operator.attrgetter('taxonomy'))
    for taxonomy, assets in assets_by_taxo.items():
        # the association with the epsilons is done in order
        assets.sort(key=operator.attrgetter('id'))
        shape = (len(assets), num_samples)
        logging.info('Building %s epsilons for taxonomy %s', shape, taxonomy)
        zeros = numpy.zeros(shape)
        epsilons = scientific.make_epsilons(zeros, seed, correlation)
        for asset, eps in zip(assets, epsilons):
            eps_dict[asset.id] = eps
    return eps_dict


def expand(array, N):
    """
    Given a non-empty array with n elements, expands it to a larger
    array with N elements.

    >>> expand([1], 3)
    array([1, 1, 1])
    >>> expand([1, 2, 3], 10)
    array([1, 2, 3, 1, 2, 3, 1, 2, 3, 1])
    >>> expand(numpy.zeros((2, 10)), 5).shape
    (5, 10)
    >>> expand([1, 2], 2)  # already expanded
    [1, 2]
    """
    n = len(array)
    if n == 0:
        raise ValueError('Empty array')
    elif n >= N:
        return array
    return numpy.array([array[i % n] for i in range(N)])


class RiskInputFromRuptures(object):
    """
    Contains all the assets associated to the given IMT and a subsets of
    the ruptures for a given calculation.

    :param imt_taxonomies: list given by the risk model
    :param sitecol: SiteCollection instance
    :param assets_by_site: list of list of assets
    :param ses_ruptures: ordered array of SESRuptures
    :param gsims: list of GSIM instances
    :param trunc_level: truncation level for the GSIMs
    :param correl_model: correlation model for the GSIMs
    :params eps_dict: a dictionary asset_id -> epsilons
    :param rup_slice: a slice object specifying which ruptures are in
    """
    def __init__(self, imt_taxonomies, sitecol, ses_ruptures,
                 gsims, trunc_level, correl_model, num_epsilons, rup_slice):
        self.imt_taxonomies = imt_taxonomies
        self.sitecol = sitecol
        self.ses_ruptures = numpy.array(ses_ruptures)
        self.col_id = ses_ruptures[0].col_id
        self.gsims = gsims
        self.trunc_level = trunc_level
        self.correl_model = correl_model
        self.weight = len(ses_ruptures)
        self.rup_slice = rup_slice
        self.imts = sorted(set(imt for imt, _ in imt_taxonomies))
        self.num_epsilons = num_epsilons

    @property
    def tags(self):
        """
        :returns:
            the tags of the underlying ruptures, which are assumed to
            be already sorted.
        """
        return [sr.tag for sr in self.ses_ruptures]

    def compute_expand_gmfs(self):
        """
        :returns:
            an array R x N where N is the number of sites and
            R is the number of ruptures.
        """
        from openquake.calculators.event_based import make_gmfs
        gmfs = make_gmfs(
            self.ses_ruptures, self.sitecol, self.imts,
            self.gsims, self.trunc_level, self.correl_model, DummyMonitor())
        gmf_dt = gsim_imt_dt(self.gsims, self.imts)
        N = len(self.sitecol.complete)
        R = len(gmfs)
        gmfa = numpy.zeros((R, N), gmf_dt)
        for i, sesrup, gmf in zip(range(R), self.ses_ruptures, gmfs):
            expanded_gmf = numpy.zeros(N, gmf_dt)
            expanded_gmf[sesrup.indices] = gmf
            gmfa[i] = expanded_gmf
        return gmfa  # array R x N

    def get_all(self, rlzs_assoc, assets_by_site, eps_dict):
        """
        :returns:
            lists of assets, hazards and epsilons
        """
        indices = [sr.ordinal % self.num_epsilons for sr in self.ses_ruptures]
        assets, hazards, epsilons = [], [], []
        gmfs = self.compute_expand_gmfs()
        gsims = list(map(str, self.gsims))
        trt_id = rlzs_assoc.csm_info.get_trt_id(self.col_id)
        for assets_, hazard in zip(assets_by_site, gmfs.T):
            haz_by_imt_rlz = {imt: {} for imt in self.imts}
            for gsim in gsims:
                for imt in self.imts:
                    for rlz in rlzs_assoc[trt_id, gsim]:
                        haz_by_imt_rlz[imt][rlz] = hazard[gsim][imt]
            for asset in assets_:
                assets.append(asset)
                hazards.append(haz_by_imt_rlz)
                eps = expand(eps_dict[asset.id][indices],
                             len(self.ses_ruptures))
                epsilons.append(eps)
        return assets, hazards, epsilons

    def __repr__(self):
        return '<%s IMT_taxonomies=%s, weight=%d>' % (
            self.__class__.__name__, self.imt_taxonomies, self.weight)
