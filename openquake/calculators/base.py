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

import sys
import abc
import pdb
import logging
import operator
import traceback
import collections

import numpy

from openquake.hazardlib.geo import geodetic
from openquake.baselib import general
from openquake.baselib.performance import DummyMonitor
from openquake.commonlib import (
    readinput, datastore, logictree, export, source, __version__)
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib.parallel import apply_reduce
from openquake.risklib import riskinput
from openquake.baselib.python3compat import with_metaclass

get_taxonomy = operator.attrgetter('taxonomy')
get_weight = operator.attrgetter('weight')
get_trt = operator.attrgetter('trt_model_id')
get_imt = operator.attrgetter('imt')

calculators = general.CallableDict(operator.attrgetter('calculation_mode'))

Site = collections.namedtuple('Site', 'sid lon lat')


class AssetSiteAssociationError(Exception):
    """Raised when there are no hazard sites close enough to any asset"""

rlz_dt = numpy.dtype([('uid', (bytes, 200)), ('weight', float)])


class BaseCalculator(with_metaclass(abc.ABCMeta)):
    """
    Abstract base class for all calculators.

    :param oqparam: OqParam object
    :param monitor: monitor object
    :param calc_id: numeric calculation ID
    """
    sitemesh = datastore.persistent_attribute('sitemesh')
    sitecol = datastore.persistent_attribute('sitecol')
    rlzs_assoc = datastore.persistent_attribute('rlzs_assoc')
    realizations = datastore.persistent_attribute('realizations')
    assets_by_site = datastore.persistent_attribute('assets_by_site')
    assetcol = datastore.persistent_attribute('assetcol')
    cost_types = datastore.persistent_attribute('cost_types')
    taxonomies = datastore.persistent_attribute('taxonomies')
    job_info = datastore.persistent_attribute('job_info')
    source_chunks = datastore.persistent_attribute('source_chunks')
    performance = datastore.persistent_attribute('performance')
    csm = datastore.persistent_attribute('composite_source_model')
    pre_calculator = None  # to be overridden
    is_stochastic = False  # True for scenario and event based calculators

    def __init__(self, oqparam, monitor=DummyMonitor(), calc_id=None,
                 persistent=True):
        self.monitor = monitor
        if persistent:
            self.datastore = datastore.DataStore(calc_id)
            self.monitor.hdf5path = self.datastore.hdf5path
        else:
            self.datastore = general.AccumDict()
            self.datastore.hdf5 = {}
            self.datastore.attrs = {}
        self.datastore.export_dir = oqparam.export_dir
        self.oqparam = oqparam
        self.persistent = persistent

    def save_params(self, **kw):
        """
        Update the current calculation parameters
        """
        vars(self.oqparam).update(kw)
        for name, val in self.oqparam.to_params():
            self.datastore.attrs[name] = val
        self.datastore.attrs['oqlite_version'] = repr(__version__)
        self.datastore.hdf5.flush()

    def set_log_format(self):
        """Set the format of the root logger"""
        fmt = '[%(asctime)s #{} %(levelname)s] %(message)s'.format(
                self.datastore.calc_id)
        for handler in logging.root.handlers:
            handler.setFormatter(logging.Formatter(fmt))

    def run(self, pre_execute=True, clean_up=True, concurrent_tasks=None,
            **kw):
        """
        Run the calculation and return the exported outputs.
        """
        self.set_log_format()
        if concurrent_tasks is not None:
            self.oqparam.concurrent_tasks = concurrent_tasks
        self.save_params(**kw)
        exported = {}
        try:
            if pre_execute:
                self.pre_execute()
            result = self.execute()
            self.post_execute(result)
            exported = self.export()
        except:
            if kw.get('pdb'):  # post-mortem debug
                tb = sys.exc_info()[2]
                traceback.print_exc(tb)
                pdb.post_mortem(tb)
            else:
                logging.critical('', exc_info=True)
                raise
        # don't cleanup if there is a critical error, otherwise
        # there will likely be a cleanup error covering the real one
        if clean_up:
            self.clean_up()
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

    def export(self, exports=None):
        """
        Export all the outputs in the datastore in the given export formats.

        :returns: dictionary output_key -> sorted list of exported paths
        """
        exported = {}
        individual_curves = self.oqparam.individual_curves
        fmts = exports.split(',') if exports else self.oqparam.exports
        for fmt in fmts:
            if not fmt:
                continue
            for key in self.datastore:  # top level keys
                if 'rlzs' in key and not individual_curves:
                    continue  # skip individual curves
                ekey = (key, fmt)
                if ekey not in export.export:  # non-exportable output
                    continue
                exported[ekey] = export.export(ekey, self.datastore)
                logging.info('exported %s: %s', key, exported[ekey])
        return exported

    def clean_up(self):
        """
        Collect the realizations and the monitoring information,
        then close the datastore.
        """
        if 'rlzs_assoc' in self.datastore:
            self.realizations = numpy.array(
                [(r.uid, r.weight) for r in self.rlzs_assoc.realizations],
                rlz_dt)
        # the datastore must not be closed, it will be closed automatically


class HazardCalculator(BaseCalculator):
    """
    Base class for hazard calculators based on source models
    """
    riskmodel = datastore.persistent_attribute('riskmodel')

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

        siteobjects = geodetic.GeographicObjects(
            Site(sid, lon, lat) for sid, lon, lat in
            zip(sitecol.sids, sitecol.lons, sitecol.lats))
        assets_by_sid = general.AccumDict()
        for assets in self.assets_by_site:
            if len(assets):
                lon, lat = assets[0].location
                site, _ = siteobjects.get_closest(lon, lat, maximum_distance)
                if site:
                    assets_by_sid += {site.sid: list(assets)}
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
                precalc.run()
                if 'scenario' not in self.oqparam.calculation_mode:
                    self.csm = precalc.csm
            else:  # read previously computed data
                self.datastore.set_parent(datastore.DataStore(precalc_id))
                # update oqparam with the attributes saved in the datastore
                self.oqparam = OqParam.from_(self.datastore.attrs)
                self.read_risk_data()

        else:  # we are in a basic calculator
            self.read_risk_data()
            self.read_sources()
        self.datastore.hdf5.flush()

    def read_exposure(self):
        """
        Read the exposure, the riskmodel and update the attributes .exposure,
        .sitecol, .assets_by_site, .cost_types, .taxonomies.
        """
        logging.info('Reading the exposure')
        with self.monitor('reading exposure', autoflush=True):
            self.exposure = readinput.get_exposure(self.oqparam)
            self.sitecol, self.assets_by_site = (
                readinput.get_sitecol_assets(self.oqparam, self.exposure))
            if len(self.exposure.cost_types):
                self.cost_types = self.exposure.cost_types
            self.taxonomies = numpy.array(
                sorted(self.exposure.taxonomies), '|S100')

    def load_riskmodel(self):
        """
        Read the risk model and set the attribute .riskmodel.
        The riskmodel can be empty for hazard calculations.
        Save the loss ratios (if any) in the datastore.
        """
        self.riskmodel = rm = readinput.get_risk_model(self.oqparam)
        missing = set(self.taxonomies) - set(rm.taxonomies)
        if rm and missing:
            raise RuntimeError('The exposure contains the taxonomies %s '
                               'which are not in the risk model' % missing)

        # save the loss ratios in the datastore
        pairs = [(cb.loss_type, (numpy.float64, len(cb.ratios)))
                 for cb in rm.curve_builders if cb.user_provided]
        if not pairs:
            return
        loss_ratios = numpy.zeros(len(rm), numpy.dtype(pairs))
        for cb in rm.curve_builders:
            if cb.user_provided:
                loss_ratios_lt = loss_ratios[cb.loss_type]
                for i, imt_taxo in enumerate(sorted(rm)):
                    loss_ratios_lt[i] = rm[imt_taxo].loss_ratios[cb.loss_type]
        self.datastore['loss_ratios'] = loss_ratios
        self.datastore['loss_ratios'].attrs['imt_taxos'] = sorted(rm)
        self.datastore['loss_ratios'].attrs['nbytes'] = loss_ratios.nbytes

    def read_risk_data(self):
        """
        Read the exposure (if any), the risk model (if any) and then the
        site collection, possibly extracted from the exposure.
        """
        logging.info('Reading the site collection')
        with self.monitor('reading site collection', autoflush=True):
            haz_sitecol = readinput.get_site_collection(self.oqparam)
        inputs = self.oqparam.inputs
        if 'exposure' in inputs:
            self.read_exposure()
            self.load_riskmodel()  # must be called *after* read_exposure
            num_assets = self.count_assets()
            if self.datastore.parent:
                haz_sitecol = self.datastore.parent['sitecol']
            if haz_sitecol is not None and haz_sitecol != self.sitecol:
                with self.monitor('assoc_assets_sites'):
                    self.sitecol, self.assets_by_site = \
                        self.assoc_assets_sites(haz_sitecol.complete)
                ok_assets = self.count_assets()
                num_sites = len(self.sitecol)
                logging.warn('Associated %d assets to %d sites, %d discarded',
                             ok_assets, num_sites, num_assets - ok_assets)
        elif (self.datastore.parent and 'exposure' in
              OqParam.from_(self.datastore.parent.attrs).inputs):
            logging.info('Re-using the already imported exposure')
            if not self.riskmodel:
                self.load_riskmodel()
        else:  # no exposure
            self.sitecol = haz_sitecol

        # save mesh and asset collection
        self.save_mesh()
        if hasattr(self, 'assets_by_site'):
            self.assetcol = riskinput.build_asset_collection(
                self.assets_by_site, self.oqparam.time_event)
            spec = set(self.oqparam.specific_assets)
            unknown = spec - set(self.assetcol['asset_ref'])
            if unknown:
                raise ValueError('The specific asset(s) %s are not in the '
                                 'exposure' % ', '.join(unknown))

    def save_mesh(self):
        """
        Save the mesh associated to the complete sitecol in the HDF5 file
        """
        if ('sitemesh' not in self.datastore and
                'sitemesh' not in self.datastore.parent):
            col = self.sitecol.complete
            mesh_dt = numpy.dtype([('lon', float), ('lat', float)])
            self.sitemesh = numpy.array(list(zip(col.lons, col.lats)), mesh_dt)

    def read_sources(self):
        """
        Read the composite source model (if any).
        This method must be called after read_risk_data, to be able
        to filter to sources according to the site collection.
        """
        if 'source' in self.oqparam.inputs:
            logging.info('Reading the composite source model')
            with self.monitor(
                    'reading composite source model', autoflush=True):
                self.csm = readinput.get_composite_source_model(
                    self.oqparam, self.sitecol, self.SourceProcessor,
                    self.monitor, dstore=self.datastore)
                # we could manage limits here
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

    def post_process(self):
        """For compatibility with the engine"""


class RiskCalculator(HazardCalculator):
    """
    Base class for all risk calculators. A risk calculator must set the
    attributes .riskmodel, .sitecol, .assets_by_site, .exposure
    .riskinputs in the pre_execute phase.
    """
    specific_assets = datastore.persistent_attribute('specific_assets')
    extra_args = ()  # to be overridden in subclasses

    def make_eps(self, num_ruptures):
        """
        :param num_ruptures: the size of the epsilon array for each asset
        """
        oq = self.oqparam
        with self.monitor('building epsilons', autoflush=True):
            return riskinput.make_eps(
                self.assets_by_site, num_ruptures,
                oq.master_seed, oq.asset_correlation)

    def build_riskinputs(self, hazards_by_key, eps=numpy.zeros(0)):
        """
        :param hazards_by_key:
            a dictionary key -> IMT -> array of length num_sites
        :param eps:
            a matrix of epsilons (possibly empty)
        :returns:
            a list of RiskInputs objects, sorted by IMT.
        """
        # add asset.idx as side effect
        riskinput.build_asset_collection(
            self.assets_by_site, self.oqparam.time_event)
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
                if len(eps):
                    for assets in reduced_assets:
                        for asset in assets:
                            reduced_eps[asset.idx] = eps[asset.idx]

                # collect the hazards by key into hazards by imt
                hdata = collections.defaultdict(lambda: [{} for _ in indices])
                for key, hazards_by_imt in hazards_by_key.items():
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
        all_args = ((self.riskinputs, self.riskmodel, self.rlzs_assoc) +
                    self.extra_args + (self.monitor,))
        res = apply_reduce(
            self.core_func.__func__, all_args,
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
        logging.info('Reading gmfs from file')
        sitecol, calc.tags, gmfs_by_imt = readinput.get_gmfs(calc.oqparam)
        calc.save_params()  # save number_of_ground_motion_fields and sites

        # reduce the gmfs matrices to the filtered sites
        for imt in calc.oqparam.imtls:
            gmfs_by_imt[imt] = gmfs_by_imt[imt][sitecol.indices]

        logging.info('Preparing the risk input')
        calc.rlzs_assoc = logictree.trivial_rlzs_assoc()
        return sitecol, {(0, 'FromFile'): gmfs_by_imt}

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
    for rupid, rows in sorted(gmf_by_idx.items()):
        assert len(haz_sitecol.indices) == len(rows), (
            len(haz_sitecol.indices), len(rows))
        for sid, gmv in zip(haz_sitecol.indices, rows):
            if sid in risk_indices:
                for trt_id, gsim in gmfs:
                    gmfs[trt_id, gsim][sid, rupid] = gmv[gsim]
    return haz_sitecol, gmfs
