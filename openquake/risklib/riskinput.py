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

import itertools
import operator
import logging
import collections

import numpy

from openquake.baselib.general import groupby, block_splitter
from openquake.hazardlib.imt import from_string
from openquake.risklib import scientific


class FakeRlzsAssoc(collections.Mapping):
    """
    Used for scenario calculators, when there are no realizations.
    """
    def __init__(self, num_rlzs):
        self.realizations = range(num_rlzs)
        self.rlzs_assoc = {(i, 'FromCsv'): [] for i in self.realizations}

    def combine(self, result):
        """
        :param result: a dictionary with a non-numeric key
        :returns: a dictionary index -> value, with value in result.values()
        """
        return {i: result[key] for i, key in enumerate(sorted(result))}

    def __iter__(self):
        return self.rlzs_assoc.iterkeys()

    def __getitem__(self, key):
        return self.rlzs_assoc[key]

    def __len__(self):
        return len(self.rlzs_assoc)


class RiskModel(collections.Mapping):
    """
    A container (imt, taxonomy) -> workflow.

    :param workflows: a dictionary (imt, taxonomy) -> workflow
    :param damage_states: None or a list of damage states
    """
    def __init__(self, workflows, damage_states=None):
        self.damage_states = damage_states  # not None for damage calculations
        self._workflows = workflows

    def get_loss_types(self):
        """
        :returns: a sorted list with all the loss_types contained in the model
        """
        return sorted(set(sum([w.loss_types for w in self.values()], [])))

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
        for imt, group in itertools.groupby(sorted(self), key=by_imt):
            yield imt, map(by_taxo, group)

    def __getitem__(self, imt_taxo):
        return self._workflows[imt_taxo]

    def __iter__(self):
        return iter(sorted(self._workflows))

    def __len__(self):
        return len(self._workflows)

    def build_input(self, imt, hazards_by_site, assets_by_site, eps_dict=None,
                    epsilon_sampling=None):
        """
        :param imt: an Intensity Measure Type
        :param hazards_by_site: an array of hazards per each site
        :param assets_by_site: an array of assets per each site
        :param eps_dict: a dictionary of epsilons per each asset
        :param epsilon_sampling: the maximum number of epsilons per asset
        :returns: a :class:`RiskInput` instance
        """
        imt_taxonomies = [(imt, self.get_taxonomies(imt))]
        return RiskInput(imt_taxonomies, hazards_by_site,
                         assets_by_site, eps_dict)

    def build_inputs_from_ruptures(self, sitecol, assets_by_site, ses_ruptures,
                                   gsims, trunc_level, correl_model, eps_dict,
                                   epsilon_sampling):
        """
        :param imt: an Intensity Measure Type
        :param sitecol: a SiteCollection instance
        :param assets_by_site: an array of assets per each site
        :param ses_ruptures: a list of SESRupture instances
        :param gsims: a list of GSIM instances
        :param trunc_level: the truncation level (or None)
        :param correl_model: the correlation model (or None)
        :param eps_dict: a dictionary asset_ref -> epsilon array
        :param epsilon_sampling: the maximum number of epsilons per asset
        :returns: a :class:`RiskInputFromRuptures` instance
        """
        imt_taxonomies = list(self.get_imt_taxonomies())
        return [RiskInputFromRuptures(
            imt_taxonomies, sitecol, assets_by_site, ruptures,
            gsims, trunc_level, correl_model, eps_dict)
            for ruptures in block_splitter(ses_ruptures, epsilon_sampling)]

    def gen_outputs(self, riskinputs, rlzs_assoc, monitor):
        """
        Group the assets per taxonomy and compute the outputs by using the
        underlying workflows. Yield the outputs generated as dictionaries
        out_by_rlz.

        :param riskinputs: a list of riskinputs with consistent IMT
        :param rlzs_assoc: a RlzsAssoc instance
        :param monitor: a monitor object used to measure the performance
        """
        mon_hazard = monitor('getting hazard')
        mon_risk = monitor('computing individual risk')
        for riskinput in riskinputs:
            with mon_hazard:
                # get assets, hazards, epsilons
                a, h, e = riskinput.get_all(rlzs_assoc)
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
                            yield out_by_rlz
        mon_hazard.flush()
        mon_risk.flush()


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

    def get_all(self, rlzs_assoc):
        """
        :returns:
            lists of assets, hazards and epsilons
        """
        assets, hazards, epsilons = [], [], []
        for hazard, assets_ in zip(self.hazard_by_site, self.assets_by_site):
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
    for taxonomy, assets in assets_by_taxo.iteritems():
        shape = (len(assets), num_samples)
        logging.info('Building %s epsilons for taxonomy %s', shape, taxonomy)
        zeros = numpy.zeros(shape)
        epsilons = scientific.make_epsilons(zeros, seed, correlation)
        for asset, eps in zip(assets, epsilons):
            eps_dict[asset.id] = eps
    return eps_dict


def expand(array, N, indices=None):
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
    return numpy.array([array[i % n] for i in indices or xrange(N)])


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
    """
    def __init__(self, imt_taxonomies, sitecol, assets_by_site, ses_ruptures,
                 gsims, trunc_level, correl_model, eps_dict):
        self.imt_taxonomies = imt_taxonomies
        self.sitecol = sitecol
        self.assets_by_site = assets_by_site
        self.ses_ruptures = numpy.array(ses_ruptures)
        self.trt_id = ses_ruptures[0].trt_model_id
        self.col_idx = ses_ruptures[0].col_idx
        self.gsims = gsims
        self.trunc_level = trunc_level
        self.correl_model = correl_model
        self.weight = len(ses_ruptures)
        self.eps_dict = eps_dict
        self.imts = sorted(set(imt for imt, _ in imt_taxonomies))

    @property
    def tags(self):
        """
        :returns:
            the tags of the underlying ruptures, which are assumed to
            be already sorted.
        """
        return [sr.tag for sr in self.ses_ruptures]

    def compute_expand_gmf(self):
        """
        :returns:
            a list of hazard dictionaries, one for each site; each
            dictionary for each key contains a dictionary IMT->array(N, R)
            where N is the number of sites and R is the number of ruptures.
        """
        from openquake.commonlib.calculators.event_based import make_gmf_by_key
        ddic = make_gmf_by_key(
            self.ses_ruptures, self.sitecol, map(from_string, self.imts),
            self.gsims, self.trunc_level, self.correl_model)
        for key, gmf_by_tag in ddic.iteritems():
            items = sorted(gmf_by_tag.iteritems())
            ddic[key] = {  # build N x R matrices
                imt: numpy.array(
                    [gmf.r_sites.expand(gmf[imt], 0) for tag, gmf in items]).T
                for imt in self.imts}
        return ddic

    def get_all(self, rlzs_assoc):
        """
        :returns:
            lists of assets, hazards and epsilons
        """
        assets, hazards, epsilons = [], [], []
        hazard_by_key_imt = self.compute_expand_gmf()
        for i, assets_ in enumerate(self.assets_by_site):
            haz_by_imt_rlz = {imt: {} for imt in self.imts}
            for key in hazard_by_key_imt:
                for imt in hazard_by_key_imt[key]:
                    hazard = hazard_by_key_imt[key][imt][i]
                    for rlz in rlzs_assoc[key]:
                        haz_by_imt_rlz[imt][rlz] = hazard
            for asset in assets_:
                assets.append(asset)
                hazards.append(haz_by_imt_rlz)
                epsilons.append(self.eps_dict[asset.id])
        return assets, hazards, epsilons

    def __repr__(self):
        return '<%s IMT_taxonomies=%s, weight=%d>' % (
            self.__class__.__name__, self.imt_taxonomies, self.weight)
