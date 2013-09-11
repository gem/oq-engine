# -*- coding: utf-8 -*-

# Copyright (c) 2012-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Hazard getters for Risk calculators.

A HazardGetter is responsible fo getting hazard outputs needed by a risk
calculation.
"""

import itertools
import collections
import numpy
import scipy

import cPickle as pickle

from openquake.hazardlib import geo, const
from openquake.hazardlib.calc import filters
from openquake.hazardlib.calc.gmf import ground_motion_field_with_residuals

from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.performance import DummyMonitor, LightMonitor
from openquake.engine.calculators.hazard import general
from openquake.engine.input import logictree

#: Scaling constant do adapt to the postgis functions (that work with
#: meters)
KILOMETERS_TO_METERS = 1000


class HazardGetter(object):
    """
    Base abstract class of an Hazard Getter.

    An Hazard Getter is used to query for the closest hazard data for
    each given asset. An Hazard Getter must be pickable such that it
    should be possible to use different strategies (e.g. distributed
    or not, using postgis or not).

    :attr hazard_outputs:
        A list of hazard output container instances (e.g. HazardCurve)

    :attr assets:
        The assets for which we wants to compute.

    :attr max_distance:
        The maximum distance, in kilometers, to use.

    :attr imt:
        The imt (in long form) for which data have to be retrieved
    """
    def __init__(self, hazard_outputs, assets, max_distance, imt):
        self.hazard_outputs = hazard_outputs
        self.assets = assets
        self.max_distance = max_distance
        self.imt = imt
        self.imt_type, self.sa_period, self.sa_damping = models.parse_imt(imt)
        # FIXME(lp). It is better to directly store the convex hull
        # instead of the mesh. We are not doing it because
        # hazardlib.Polygon is not (yet) pickeable
        self._assets_mesh = geo.mesh.Mesh.from_points_list([
            geo.point.Point(asset.site.x, asset.site.y)
            for asset in self.assets])
        self.asset_dict = dict((asset.id, asset) for asset in self.assets)

    def __repr__(self):
        return "<%s max_distance=%s assets=%s>" % (
            self.__class__.__name__, self.max_distance,
            [a.id for a in self.assets])

    def get_data(self, hazard_output, monitor):
        """
        Subclasses must implement this.
        """
        raise NotImplementedError

    def get_assets_data(self, hazard_output, monitor=None):
        """
        :param monitor: a performance monitor or None
        :returns:
            A tuple with two elements. The first is an array of instances of
            :class:`openquake.engine.db.models.ExposureData`, the second is
            the corresponding hazard data.
        """
        monitor = monitor or DummyMonitor()
        assets, data = self.get_data(hazard_output, monitor)
        missing_asset_ids = set(self.asset_dict) - set(a.id for a in assets)

        for missing_asset_id in missing_asset_ids:
            logs.LOG.warn(
                "No hazard with imt %s has been found for "
                "the asset %s within %s km" % (
                    self.imt,
                    self.asset_dict[missing_asset_id],
                    self.max_distance))

        return assets, data

    def __call__(self, monitor=None):
        for hazard in self.hazard_outputs:
            h = hazard.output_container
            yield (hazard.id,) + self.get_assets_data(h, monitor)

    def weights(self):
        ws = []
        for hazard in self.hazard_outputs:
            h = hazard.output_container
            if hasattr(h, 'lt_realization') and h.lt_realization:
                ws.append(h.lt_realization.weight)
        return ws


class HazardCurveGetterPerAsset(HazardGetter):
    """
    Simple HazardCurve Getter that performs a spatial query for each
    asset.

    :attr imls:
        The intensity measure levels of the curves we are going to get.
    """

    def get_data(self, hazard_output, monitor):
        """
        Calls ``get_by_site`` for each asset and pack the results as
        requested by the :meth:`HazardGetter.get_data` interface.
        """
        hc = hazard_output

        if hc.output.output_type == 'hazard_curve':
            imls = hc.imls
        elif hc.output.output_type == 'hazard_curve_multi':
            hc = models.HazardCurve.objects.get(
                output__oq_job=hc.output.oq_job,
                output__output_type='hazard_curve',
                statistics=hc.statistics,
                lt_realization=hc.lt_realization,
                imt=self.imt_type,
                sa_period=self.sa_period,
                sa_damping=self.sa_damping)
            imls = hc.imls

        with monitor.copy('getting closest hazard curves'):
            assets = []
            curves = []

            for asset in self.assets:
                queryset = self.get_by_site(asset.site, hc.id)
                if queryset is not None:
                    [poes] = queryset
                    assets.append(asset)
                    curves.append(zip(imls, poes))

        return assets, curves

    def get_by_site(self, site, hazard_id):
        """
        :param site:
            An instance of :class:`django.contrib.gis.geos.point.Point`
            corresponding to the location of an asset.
        """
        cursor = models.getcursor('job_init')

        query = """
        SELECT hzrdr.hazard_curve_data.poes
        FROM hzrdr.hazard_curve_data
        WHERE hazard_curve_id = %s
        AND ST_DWithin(ST_GeographyFromText(%s), location::geography, %s)
        ORDER BY
            ST_Distance(location::geography, ST_GeographyFromText(%s), false)
        LIMIT 1
        """

        args = (hazard_id, site.wkt, self.max_distance * KILOMETERS_TO_METERS,
                site.wkt)

        cursor.execute(query, args)
        return cursor.fetchone()


class GroundMotionValuesGetter(HazardGetter):
    """
    Hazard getter for loading ground motion values. It is instantiated
    with a set of assets all of the same taxonomy.
    """

    def __init__(self, hazard, assets, max_distance, imt, seeds=None):
        super(GroundMotionValuesGetter, self).__init__(
            hazard, assets, max_distance, imt)
        assert hazard[0].output_type != "ses" or seeds is not None
        self.seeds = seeds or [None] * len(hazard)

    def __call__(self, monitor=None):
        """
        Override base method to seed the rng for each hazard output
        """
        for hazard, seed in zip(self.hazard_outputs, self.seeds):
            h = hazard.output_container
            numpy.random.seed(seed)
            yield (hazard.id,) + self.get_assets_data(h, monitor)

    def assets_gen(self, hazard_output):
        """
        Iterator yielding site_id, assets.
        """
        cursor = models.getcursor('job_init')
        # NB: the ``distinct ON (exposure_data.id)`` combined with the
        # ``ORDER BY ST_Distance`` does the job to select the closest site.
        # The other ORDER BY are there to help debugging, it is always
        # nice to have numbers coming in a fixed order. They have an
        # insignificant effect on the performance.
        query = """
SELECT site_id, array_agg(asset_id ORDER BY asset_id) AS asset_ids FROM (
  SELECT DISTINCT ON (exp.id) exp.id AS asset_id, hsite.id AS site_id
  FROM riski.exposure_data AS exp
  JOIN hzrdi.hazard_site AS hsite
  ON ST_DWithin(exp.site, hsite.location, %s)
  WHERE hsite.hazard_calculation_id = %s
  AND taxonomy = %s AND exposure_model_id = %s AND exp.site && %s
  ORDER BY exp.id, ST_Distance(exp.site, hsite.location, false)) AS x
GROUP BY site_id ORDER BY site_id;
   """
        args = (self.max_distance * KILOMETERS_TO_METERS,
                hazard_output.output.oq_job.hazard_calculation.id,
                self.assets[0].taxonomy,
                self.assets[0].exposure_model_id,
                self._assets_mesh.get_convex_hull().wkt)
        cursor.execute(query, args)
        sites_assets = cursor.fetchall()
        if not sites_assets:
            logs.LOG.warn('No close site found for %d assets of taxonomy %s',
                          len(self.assets), self.assets[0].taxonomy)
        for site_id, asset_ids in sites_assets:
            assets = [self.asset_dict[i] for i in asset_ids
                      if i in self.asset_dict]
            # notice the "if i in self.asset_dict": in principle, it should
            # not be necessary; in practice, the query may returns spurious
            # assets not in the initial set; this is why we are filtering
            # the spurious assets; it is a mysterious behaviour of PostGIS
            if assets:
                yield site_id, assets

    def get_gmvs_ruptures(self, gmf, site_id):
        """
        :returns: gmvs and ruptures for the given site and IMT
        """
        gmvs = []
        ruptures = []

        for gmf in models.GmfData.objects.filter(
                gmf=gmf,
                site=site_id, imt=self.imt_type, sa_period=self.sa_period,
                sa_damping=self.sa_damping):
            gmvs.extend(gmf.gmvs)
            if gmf.rupture_ids:
                ruptures.extend(gmf.rupture_ids)
        if not gmvs:
            logs.LOG.warn('No gmvs for site %s, IMT=%s', site_id, self.imt)
        return gmvs, ruptures

    def get_data(self, hazard_output, monitor):
        """
        :returns: a list with all the assets and the hazard data.

        For scenario computations the data is a numpy.array
        with the GMVs; for event based computations the data is
        a pair (GMVs, rupture_ids).
        """

        all_ruptures = set()
        all_assets = []
        all_gmvs = []
        site_gmv = collections.OrderedDict()
        # dictionary site -> ({rupture_id: gmv}, n_assets)
        # the ordering is there only to have repeatable runs
        with monitor.copy('associating assets->site'):
            site_assets = list(self.assets_gen(hazard_output))

        if hazard_output.output.output_type == 'ses':
            logs.LOG.info('Compute Ground motion field values on the fly')
            return self.compute_gmvs(hazard_output, site_assets, monitor)

        with monitor.copy('getting gmvs and ruptures'):
            for site_id, assets in site_assets:
                n_assets = len(assets)
                all_assets.extend(assets)
                gmvs, ruptures = self.get_gmvs_ruptures(hazard_output, site_id)
                if ruptures:  # event based
                    site_gmv[site_id] = dict(zip(ruptures, gmvs)), n_assets
                    for r in ruptures:
                        all_ruptures.add(r)
                elif gmvs:  # scenario
                    array = numpy.array(gmvs)
                    all_gmvs.extend([array] * n_assets)
        if all_assets and not all_ruptures:  # scenario
            return all_assets, all_gmvs

        # second pass for event based, filling with zeros
        with monitor.copy('filling gmvs with zeros'):
            all_ruptures = sorted(all_ruptures)
            for site_id, (gmv, n_assets) in site_gmv.iteritems():
                array = numpy.array([gmv.get(r, 0.) for r in all_ruptures])
                gmv.clear()  # save memory
                all_gmvs.extend([array] * n_assets)
        return all_assets, (all_gmvs, all_ruptures)

    def compute_gmvs(self, hazard_output, site_assets, monitor):
        """
        Compute ground motion values on the fly
        """
        # get needed hazard calculation params from the db
        hc = hazard_output.output.oq_job.hazard_calculation
        truncation_level = hc.truncation_level
        gsims = logictree.LogicTreeProcessor(
            hc.id).parse_gmpe_logictree_path(
            hazard_output.lt_realization.gsim_lt_path)
        if hc.ground_motion_correlation_model is not None:
            model = general.get_correl_model(hc)
        else:
            model = None

        # check that the ruptures have been computed by a sufficiently
        # new version of openquake
        queryset = models.SESRupture.objects.filter(
            ses__ses_collection=hazard_output).order_by('id')

        if queryset.filter(rupture="not computed").exists():
            msg = ("The stochastic event set has been computed with "
                   " a version of openquake engine too old. "
                   "Please, re-run your hazard")
            logs.LOG.error(msg)
            raise RuntimeError(msg)
        count = queryset.count()

        # using a generator over ruptures to save memory
        def ruptures():
            cursor = models.getcursor('job_init')
            # a rupture "consumes" 8Kb. This limit actually
            # control the amount of memory used to store them
            limit = 10000
            offsets = range(0, count, limit)
            query = """
                    SELECT rup.rupture FROM hzrdr.ses_rupture AS rup
                    JOIN hzrdr.ses AS ses ON ses.id = rup.ses_id
                    WHERE ses.ses_collection_id = %s
                    ORDER BY rup.id LIMIT %s OFFSET %s"""
            for offset in offsets:
                cursor.execute(query, (hazard_output.id, limit, offset))
                for (rupture_data,) in cursor.fetchall():
                    yield pickle.loads(str(rupture_data))
        r_objs = list(ruptures())

        r_seeds = numpy.random.randint(0, models.MAX_SINT_32, count)
        r_ids = queryset.values_list('id', flat=True)

        calc_getter = GroundMotionValuesCalcGetter(
            self.imt, hc.site_collection, site_assets,
            truncation_level, gsims, model)

        r_objs, r_seeds, r_ids = [r_objs[0]], [r_seeds[0]], [r_ids[0]]
        with monitor.copy('computing gmvs'):
            all_assets, gmvs = calc_getter.compute(
                r_objs, r_seeds, r_ids, hc.maximum_distance)

        print r_objs, r_seeds, r_ids, hc.maximum_distance
        print '***', gmvs[0]
        return all_assets, (gmvs, r_ids)


class BCRGetter(object):
    def __init__(self, getter_orig, getter_retro):
        self.assets = getter_orig.assets
        self.getter_orig = getter_orig
        self.getter_retro = getter_retro

    def __call__(self, monitor):
        orig_gen = self.getter_orig(monitor)
        retro_gen = self.getter_retro(monitor)

        try:
            while 1:
                hid, assets, orig = orig_gen.next()
                _hid, _assets, retro = retro_gen.next()
                yield hid, assets, (orig, retro)
        except StopIteration:
            pass


class GroundMotionValuesCalcGetter(object):
    """
    Compute ground motion values suitable to be used for a risk event
    based calculation, given a set of ruptures computed by an hazard
    calculation
    """
    def __init__(self, imt, site_collection, sites_assets,
                 truncation_level, gsims, correlation_model):
        """
        :param str imt:
            the intensity measure type considered
        :param site_collection:
            a :class:`openquake.engine.db.models.SiteCollection` instance
            holding all the sites of the hazard calculation from which the
            ruptures have been computed
        :param sites_assets:
            an iterator over tuple of the form (site_id, assets), where
            site_id is the id of a
            :class:`openquake.engine.db.models.HazardSite` object and
            assets is a list of asset object associated to such site
        :param float truncation_level:
            the truncation level of the normal distribution used to generate
            random numbers. If none, a non-truncated normal is used
        :param gsims:
            a dictionary of the gsims considered keyed by the tectonic
            region type
        :param correlation_model:
            Instance of correlation model object. See
            :mod:`openquake.hazardlib.correlation`. Can be ``None``, in which
            case non-correlated ground motion fields are calculated.
            Correlation model is not used if ``truncation_level`` is zero.
        """

        self.imt = general.imt_to_hazardlib(imt)
        self.site_collection = site_collection
        self.sites_assets = sites_assets
        self.truncation_level = truncation_level
        self.sites = models.SiteCollection(
            [self.site_collection.get_by_id(site_id)
             for site_id, _assets in self.sites_assets])

        all_site_ids = [s.id for s in self.site_collection]
        self.sites_dict = dict((all_site_id, i)
                               for i, all_site_id in enumerate(all_site_ids))

        self.generate_epsilons = truncation_level != 0
        self.correlation_matrix = None
        if self.generate_epsilons:
            if truncation_level is None:
                self.distribution = scipy.stats.norm()
            elif truncation_level > 0:
                self.distribution = scipy.stats.truncnorm(
                    -truncation_level, truncation_level)

            if correlation_model is not None:
                c = correlation_model.get_lower_triangle_correlation_matrix(
                    site_collection, self.imt)
                self.correlation_matrix = c

        self.gsims = gsims

    def sites_of_interest(self, rupture, maximum_distance):
        """
        :param openquake.hazardlib.source.rupture.Rupture rupture:
            Rupture to calculate ground motion fields radiated from.

        :returns:
            a 2-tuple with 1) an
            :class:`openquake.engine.db.models.SiteCollection` object
            holding the sites that are within ``hazard_maximum_distance``
            from the `rupture`. 2) the indices of the filtered sites in
            the whole ``sites`` collection of fields
        """
        # filtering ruptures/sites
        rupture_sites = list(
            filters.rupture_site_distance_filter(
                maximum_distance)([(rupture, self.sites)]))
        if not rupture_sites:
            return [], []
        [(rupture, sites_filtered)] = rupture_sites

        # convert the hazard lib site collection to engine one
        # that supports a fast __contains__ method and holds the site enhanced
        # by with ids
        sites_filtered = self.sites.subcollection(sites_filtered.indices)

        # find the indices in the site collection
        site_ids_indexes = [self.sites_dict[s.id] for s in sites_filtered]
        return sites_filtered, site_ids_indexes

    def epsilons(self, rupture_seed, mask, total_residual):
        """
        :param int rupture_seed:
            a seed used to initialize the rng
        :param mask:
            the set of indices used to slice the matrices computed
        :param bool total_residual:
            True if only the matrix with the epsilons for the total
            residual should be computed
        :returns:
            Three matrices holding the epsilons for the total, inter-event,
            intra-event residuals. If `generate_epsilons` is False, all of them
            are None. If ``total_residual`` is True, the latter two are None.
            Otherwise, the first one is None.
        """
        if not self.generate_epsilons:
            return None, None, None

        # we seet the rupture_seed such that in every task we
        # always get the same numbers for a given rupture
        numpy.random.seed(rupture_seed)

        if total_residual:
            total_residual_epsilons = self.distribution.rvs(
                size=len(self.site_collection))[mask]
            return total_residual_epsilons, None, None
        else:
            inter_residual_epsilons = self.distribution.rvs(size=1)
            all_intra = self.distribution.rvs(size=len(self.site_collection))
            if self.correlation_matrix is not None:
                all_intra = numpy.array(
                    numpy.dot(self.correlation_matrix, all_intra))[0]
            intra_residual_epsilons = all_intra[mask]
            return None, inter_residual_epsilons, intra_residual_epsilons

    def gsim(self, rupture):
        """
        Shortcut to get a gsim associated with a rupture and a boolean value
        saying if such gsim is defined only for total standard deviation
        """
        gsim = self.gsims[rupture.tectonic_region_type]
        cond = gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES == set(
            [const.StdDev.TOTAL])
        return gsim, cond

    def compute(self, ruptures, rupture_seeds, rupture_ids, maximum_distance):
        """
        Compute ground motion values radiated from `ruptures`.

        :param ruptures:
            an iterator over N
            :class:`openquake.hazardlib.source.rupture.Rupture` instances
        :param rupture_seeds:
            an interator over N integer values to be used to initialize the
            RNG
        :param rupture_ids:
            an iterator over N integer values. Each of them uniquely identifies
            the corresponding `rupture`
        :param float maximum_distance:
            the maximum distance threshold used to filter the sites to be
            considered for each rupture
        :returns:
            a tuple with two elements. The first one is a list of A numpy
            array. Each of them contains the ground motion values associated
            with an asset. The second element contains the list of A assets
            considered.
        """
        all_gmvs = []
        all_assets = []

        site_gmv = collections.defaultdict(dict)
        performance_dict = collections.Counter()

        for rupture, rupture_seed, rupture_id in itertools.izip(
                ruptures, rupture_seeds, rupture_ids):

            gsim, tstddev = self.gsim(rupture)

            with LightMonitor(performance_dict, 'filtering sites'):
                sites_of_interest, mask = self.sites_of_interest(
                    rupture, maximum_distance)

            if not sites_of_interest:
                continue

            with LightMonitor(performance_dict, 'generating epsilons'):
                (total, inter, intra) = self.epsilons(
                    rupture_seed, mask, tstddev)

            with LightMonitor(
                    performance_dict, 'compute ground motion fields'):
                gmf = ground_motion_field_with_residuals(
                    rupture, sites_of_interest,
                    self.imt, gsim, self.truncation_level,
                    total_residual_epsilons=total,
                    intra_residual_epsilons=intra,
                    inter_residual_epsilons=inter)

            with LightMonitor(performance_dict, 'collecting gmvs'):
                for site, gmv in itertools.izip(sites_of_interest, gmf):
                    site_gmv[site.id][rupture_id] = gmv

        logs.LOG.debug('Disaggregation of the time spent in the loop %s' % (
            performance_dict))

        for site_id, assets in self.sites_assets:
            n_assets = len(assets)
            if site_id in site_gmv:
                gmvs = [site_gmv[site_id].get(r, 0) for r in rupture_ids]
            else:
                gmvs = numpy.zeros(len(rupture_ids))
            del site_gmv[site_id]

            all_gmvs.extend([gmvs] * n_assets)
            all_assets.extend(assets)

        return all_assets, all_gmvs
