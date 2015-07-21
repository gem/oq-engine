#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014-2015, GEM Foundation

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

import os
import sys
import abc
import logging
import operator
import collections

import numpy

from openquake.hazardlib.geo import geodetic
from openquake.baselib import general
from openquake.baselib.performance import DummyMonitor
from openquake.commonlib import readinput, datastore, logictree, export, source
from openquake.commonlib.parallel import apply_reduce
from openquake.risklib import riskinput

get_taxonomy = operator.attrgetter('taxonomy')
get_weight = operator.attrgetter('weight')
get_trt = operator.attrgetter('trt_model_id')
get_imt = operator.attrgetter('imt')

calculators = general.CallableDict(operator.attrgetter('calculation_mode'))


class AssetSiteAssociationError(Exception):
    """Raised when there are no hazard sites close enough to any asset"""

rlz_dt = numpy.dtype([('uid', (str, 200)), ('weight', float)])


class BaseCalculator(object):
    """
    Abstract base class for all calculators.

    :param oqparam: OqParam object
    :param monitor: monitor object
    :param calc_id: numeric calculation ID
    """
    __metaclass__ = abc.ABCMeta

    oqparam = datastore.persistent_attribute('oqparam')
    sitemesh = datastore.persistent_attribute('sitemesh')
    sitecol = datastore.persistent_attribute('sitecol')
    rlzs_assoc = datastore.persistent_attribute('rlzs_assoc')
    realizations = datastore.persistent_attribute('realizations')
    assets_by_site = datastore.persistent_attribute('assets_by_site')
    assetcol = datastore.persistent_attribute('assetcol')
    cost_types = datastore.persistent_attribute('cost_types')
    taxonomies = datastore.persistent_attribute('taxonomies')
    job_info = datastore.persistent_attribute('job_info')
    source_info = datastore.persistent_attribute('source_info')
    performance = datastore.persistent_attribute('performance')
    csm = datastore.persistent_attribute('composite_source_model')
    pre_calculator = None  # to be overridden
    is_stochastic = False  # True for scenario and event based calculators

    def __init__(self, oqparam, monitor=DummyMonitor(), calc_id=None,
                 persistent=True):
        self.monitor = monitor
        if persistent:
            self.datastore = datastore.DataStore(calc_id)
        else:
            self.datastore = general.AccumDict()
            self.datastore.hdf5 = {}
        self.datastore.export_dir = oqparam.export_dir
        if 'oqparam' not in self.datastore:  # new datastore
            self.oqparam = oqparam
        # else we are doing a precalculation; oqparam has been already stored
        self.persistent = persistent

    def run(self, pre_execute=True, clean_up=True, concurrent_tasks=None,
            **kw):
        """
        Run the calculation and return the exported outputs.
        """
        if concurrent_tasks is not None:
            self.oqparam.concurrent_tasks = concurrent_tasks
        vars(self.oqparam).update(kw)
        exported = {}
        try:
            if pre_execute:
                with self.monitor('pre_execute', autoflush=True):
                    self.pre_execute()
            with self.monitor('execute', autoflush=True):
                result = self.execute()
            with self.monitor('post_execute', autoflush=True):
                self.post_execute(result)
            with self.monitor('export', autoflush=True):
                exported = self.export()
        finally:
            etype = sys.exc_info()[0]
            if etype:
                logging.critical('', exc_info=True)
            if clean_up:
                try:
                    self.clean_up()
                except:
                    logging.error('Cleanup error', exc_info=True)
            return exported

    def core_func(*args):
        """
        Core routine running on the workers.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def pre_execute(self):
        """
        Initialization phase.
        """

    @abc.abstractmethod
    def execute(self):
        """
        Execution phase. Usually will run in parallel the core
        function and return a dictionary with the results.
        """

    @abc.abstractmethod
    def post_execute(self, result):
        """
        Post-processing phase of the aggregated output. It must be
        overridden with the export code. It will return a dictionary
        of output files.
        """

    def export(self):
        """
        Export all the outputs in the datastore in the given export formats.

        :returns: dictionary output_key -> sorted list of exported paths
        """
        exported = {}
        individual_curves = self.oqparam.individual_curves
        for fmt in self.oqparam.exports:
            if not fmt:
                continue
            for key in self.datastore:
                if 'rlzs' in key and not individual_curves:
                    continue  # skip individual curves
                ekey = (key, fmt)
                try:
                    exported[ekey] = sorted(
                        export.export(ekey, self.datastore))
                    logging.info('exported %s: %s', key, exported[ekey])
                except KeyError:
                    logging.info('%s is not exportable in %s', key, fmt)
        return exported

    def clean_up(self):
        """
        Collect the realizations and the monitoring information,
        then close the datastore.
        """
        self.realizations = numpy.array(
            [(r.uid, r.weight) for r in self.rlzs_assoc.realizations], rlz_dt)
        performance = self.monitor.collect_performance()
        if performance is not None:
            self.performance = performance
        self.datastore.close()
        self.datastore.symlink(os.path.dirname(self.oqparam.inputs['job_ini']))


class HazardCalculator(BaseCalculator):
    """
    Base class for hazard calculators based on source models
    """
    mean_curves = None  # to be overridden
    SourceProcessor = source.SourceFilterSplitter

    def assoc_assets_sites(self, sitecol):
        """
        :param sitecol: a sequence of sites
        :returns: a pair (filtered_sites, assets_by_site)

        The new site collection is different from the original one
        if some assets were discarded because of the asset_hazard_distance
        or if there were missing assets for some sites.
        """
        maximum_distance = self.oqparam.asset_hazard_distance

        def getlon(site):
            return site.location.longitude

        def getlat(site):
            return site.location.latitude

        siteobjects = geodetic.GeographicObjects(sitecol, getlon, getlat)
        assets_by_sid = general.AccumDict()
        for assets in self.assets_by_site:
            if len(assets):
                lon, lat = assets[0].location
                site = siteobjects.get_closest(lon, lat, maximum_distance)
                if site:
                    assets_by_sid += {site.id: list(assets)}
        if not assets_by_sid:
            raise AssetSiteAssociationError(
                'Could not associate any site to any assets within the '
                'maximum distance of %s km' % maximum_distance)
        mask = numpy.array([sid in assets_by_sid for sid in sitecol.sids])
        assets_by_site = [assets_by_sid.get(sid, []) for sid in sitecol.sids]
        return sitecol.filter(mask), numpy.array(assets_by_site)

    def count_assets(self):
        """
        Count how many assets are taken into consideration by the calculator
        """
        return sum(len(assets) for assets in self.assets_by_site)

    def pre_execute(self):
        """
        Check if there is a pre_calculator or a previous calculation ID.
        If yes, read the inputs by invoking the precalculator or by retrieving
        the previous calculation; if not, read the inputs directly.
        """
        if self.pre_calculator is not None:
            # the parameter hazard_calculation_id is only meaningful if
            # there is a precalculator
            precalc_id = self.oqparam.hazard_calculation_id
            if precalc_id is None:  # recompute everything
                precalc = calculators[self.pre_calculator](
                    self.oqparam, self.monitor('precalculator'),
                    self.datastore.calc_id)
                precalc.run(clean_up=False)
                if 'scenario' not in self.oqparam.calculation_mode:
                    self.csm = precalc.csm
            else:  # read previously computed data
                self.datastore.parent = datastore.DataStore(precalc_id)
                # merge old oqparam into the new ones, when possible
                new = vars(self.oqparam)
                for name, value in self.datastore.parent['oqparam']:
                    if name not in new:  # add missing parameter
                        new[name] = value
                self.oqparam = self.oqparam
                self.read_exposure_sitecol()

        else:  # we are in a basic calculator
            self.read_exposure_sitecol()
            self.read_sources()
        self.datastore.hdf5.flush()

    def read_exposure_sitecol(self):
        """
        Read the exposure (if any) and then the site collection, possibly
        extracted from the exposure.
        """
        inputs = self.oqparam.inputs
        if 'exposure' in inputs:
            logging.info('Reading the exposure')
            with self.monitor('reading exposure', autoflush=True):
                self.exposure = readinput.get_exposure(self.oqparam)
                self.sitecol, self.assets_by_site = (
                    readinput.get_sitecol_assets(self.oqparam, self.exposure))
                self.cost_types = self.exposure.cost_types
                self.taxonomies = numpy.array(
                    sorted(self.exposure.taxonomies), '|S100')
            num_assets = self.count_assets()
            if self.datastore.parent:
                haz_sitecol = self.datastore.parent['sitecol']
            elif 'gmfs' in inputs:
                haz_sitecol = readinput.get_site_collection(self.oqparam)
            # TODO: think about the case hazard_curves in inputs
            else:
                haz_sitecol = None
            if haz_sitecol is not None and haz_sitecol != self.sitecol:
                with self.monitor('assoc_assets_sites'):
                    self.sitecol, self.assets_by_site = \
                        self.assoc_assets_sites(haz_sitecol.complete)
                ok_assets = self.count_assets()
                num_sites = len(self.sitecol)
                logging.warn('Associated %d assets to %d sites, %d discarded',
                             ok_assets, num_sites, num_assets - ok_assets)
        elif (self.datastore.parent and 'exposure' in
              self.datastore.parent['oqparam'].inputs):
            logging.info('Re-using the already imported exposure')
        else:  # no exposure
            logging.info('Reading the site collection')
            with self.monitor('reading site collection', autoflush=True):
                self.sitecol = readinput.get_site_collection(self.oqparam)

        # save mesh and asset collection
        self.save_mesh()
        if hasattr(self, 'assets_by_site'):
            self.assetcol = riskinput.build_asset_collection(
                self.assets_by_site, self.oqparam.time_event)

    def save_mesh(self):
        """
        Save the mesh associated to the complete sitecol in the HDF5 file
        """
        if ('sitemesh' not in self.datastore and
                'sitemesh' not in self.datastore.parent):
            col = self.sitecol.complete
            mesh_dt = numpy.dtype([('lon', float), ('lat', float)])
            self.sitemesh = numpy.array(zip(col.lons, col.lats), mesh_dt)

    def read_sources(self):
        """
        Read the composite source model (if any).
        This method must be called after read_exposure_sitecol, to be able
        to filter to sources according to the site collection.
        """
        if 'source' in self.oqparam.inputs:
            logging.info('Reading the composite source model')
            with self.monitor(
                    'reading composite source model', autoflush=True):
                self.csm = readinput.get_composite_source_model(
                    self.oqparam, self.sitecol, self.SourceProcessor,
                    self.monitor)
                # we could manage limits here
                self.source_info = self.csm.source_info
                self.job_info = readinput.get_job_info(
                    self.oqparam, self.csm, self.sitecol)
                self.csm.count_ruptures()
                self.rlzs_assoc = self.csm.get_rlzs_assoc()

                logging.info(
                    'Total weight of the sources=%s',
                    self.job_info['input_weight'])
                logging.info(
                    'Expected output size=%s',
                    self.job_info['output_weight'])


class RiskCalculator(HazardCalculator):
    """
    Base class for all risk calculators. A risk calculator must set the
    attributes .riskmodel, .sitecol, .assets_by_site, .exposure
    .riskinputs in the pre_execute phase.
    """

    riskmodel = datastore.persistent_attribute('riskmodel')
    specific_assets = datastore.persistent_attribute('specific_assets')

    def make_eps_dict(self, num_ruptures):
        """
        :param num_ruptures: the size of the epsilon array for each asset
        """
        oq = self.oqparam
        with self.monitor('building epsilons', autoflush=True):
            eps = riskinput.make_eps_dict(
                self.assets_by_site, num_ruptures,
                oq.master_seed, oq.asset_correlation)
            return eps

    def build_riskinputs(self, hazards_by_key, eps_dict=None):
        """
        :param hazards_by_key:
            a dictionary key -> IMT -> array of length num_sites
        :returns:
            a list of RiskInputs objects, sorted by IMT.
        """
        imtls = self.oqparam.imtls
        with self.monitor('building riskinputs', autoflush=True):
            riskinputs = []
            idx_weight_pairs = [
                (i, len(assets))
                for i, assets in enumerate(self.assets_by_site)]
            blocks = general.split_in_blocks(
                idx_weight_pairs,
                self.oqparam.concurrent_tasks or 1,
                weight=operator.itemgetter(1))
            for block in blocks:
                indices = numpy.array([idx for idx, _weight in block])
                reduced_assets = self.assets_by_site[indices]
                reduced_eps = {}  # for the assets belonging to the indices
                if eps_dict:
                    for assets in reduced_assets:
                        for asset in assets:
                            reduced_eps[asset.id] = eps_dict[asset.id]

                # collect the hazards by key into hazards by imt
                hdata = collections.defaultdict(lambda: [{} for _ in indices])
                for key, hazards_by_imt in hazards_by_key.iteritems():
                    for imt in imtls:
                        hazards_by_site = hazards_by_imt[imt]
                        for i, haz in enumerate(hazards_by_site[indices]):
                            hdata[imt][i][key] = haz
                # build the riskinputs
                for imt in hdata:
                    ri = self.riskmodel.build_input(
                        imt, hdata[imt], reduced_assets, reduced_eps)
                    if ri.weight > 0:
                        riskinputs.append(ri)
            logging.info('Built %d risk inputs', len(riskinputs))
            return sorted(riskinputs, key=self.riskinput_key)

    def riskinput_key(self, ri):
        """
        :param ri: riskinput object
        :returns: the IMT associated to it
        """
        return ri.imt

    def pre_execute(self):
        """
        Set the attributes .riskmodel, .sitecol, .assets_by_site
        """
        HazardCalculator.pre_execute(self)
        self.riskmodel = readinput.get_risk_model(self.oqparam)
        if hasattr(self, 'exposure'):
            missing = self.exposure.taxonomies - set(
                self.riskmodel.get_taxonomies())
            if missing:
                raise RuntimeError('The exposure contains the taxonomies %s '
                                   'which are not in the risk model' % missing)

    def execute(self):
        """
        Parallelize on the riskinputs and returns a dictionary of results.
        Require a `.core_func` to be defined with signature
        (riskinputs, riskmodel, rlzs_assoc, monitor).
        """
        # add fatalities as side effect
        riskinput.build_asset_collection(
            self.assets_by_site, self.oqparam.time_event)
        self.monitor.oqparam = self.oqparam
        if self.pre_calculator == 'event_based_rupture':
            self.monitor.assets_by_site = self.assets_by_site
            self.monitor.num_assets = self.count_assets()
        res = apply_reduce(
            self.core_func.__func__,
            (self.riskinputs, self.riskmodel, self.rlzs_assoc, self.monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=get_weight, key=self.riskinput_key)
        return res


# functions useful for the calculators ScenarioDamage and ScenarioRisk

def get_gmfs(calc):
    """
    :param calc: a ScenarioDamage or ScenarioRisk calculator
    :returns: a dictionary of gmfs
    """
    if 'gmfs' in calc.oqparam.inputs:  # from file
        return read_gmfs_from_csv(calc)
    # else from rupture
    gmf = calc.datastore['gmfs/col00'].value
    # NB: if the hazard site collection has N sites, the hazard
    # filtered site collection for the nonzero GMFs has N' <= N sites
    # whereas the risk site collection associated to the assets
    # has N'' <= N' sites
    if calc.datastore.parent:
        haz_sitecol = calc.datastore.parent['sitecol']  # N' values
    else:
        haz_sitecol = calc.sitecol
    risk_indices = set(calc.sitecol.indices)  # N'' values
    N = len(haz_sitecol.complete)
    imt_dt = numpy.dtype([(imt, float) for imt in calc.oqparam.imtls])
    gmf_by_idx = general.groupby(gmf, lambda row: row['idx'])
    R = len(gmf_by_idx)
    # build a matrix N x R for each GSIM realization
    gmfs = {(trt_id, gsim): numpy.zeros((N, R), imt_dt)
            for trt_id, gsim in calc.rlzs_assoc}
    for rupid, rows in sorted(gmf_by_idx.iteritems()):
        for sid, gmv in zip(haz_sitecol.indices, rows):
            if sid in risk_indices:
                for trt_id, gsim in gmfs:
                    gmfs[trt_id, gsim][sid, rupid] = gmv[gsim]
    return gmfs


def read_gmfs_from_csv(calc):
    """
    :param calc: a ScenarioDamage or ScenarioRisk calculator
    :returns: riskinputs
    """
    logging.info('Reading hazard curves from CSV')
    gmfs_by_imt = readinput.get_gmfs(calc.oqparam, calc.sitecol.complete)

    # reduce the gmfs matrices to the filtered sites
    for imt in calc.oqparam.imtls:
        gmfs_by_imt[imt] = gmfs_by_imt[imt][calc.sitecol.indices]

    num_assets = calc.count_assets()
    num_sites = len(calc.sitecol)
    logging.info('Associated %d assets to %d sites', num_assets, num_sites)

    logging.info('Preparing the risk input')
    fake_rlz = logictree.Realization(
        value=('FromCsv',), weight=1, lt_path=('',),
        ordinal=0, lt_uid=('*',))
    calc.rlzs_assoc = logictree.RlzsAssoc([fake_rlz])
    return {(0, 'FromCsv'): gmfs_by_imt}
