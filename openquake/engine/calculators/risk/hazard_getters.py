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
from openquake.hazardlib.imt import from_string

from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.performance import DummyMonitor, LightMonitor
from openquake.engine.calculators.hazard import general

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
        self.imt_type, self.sa_period, self.sa_damping = from_string(imt)
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
        if not assets:
            logs.LOG.warn(
                'No hazard site found within the maximum distance of %f km for'
                ' %d assets of taxonomy %s, IMT=%s: %s', self.max_distance,
                len(self.assets), self.assets[0].taxonomy, self.imt,
                ' '.join(a.asset_ref for a in self.assets))
            return [], []

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
            assets, data = self.get_assets_data(h, monitor)
            if len(assets) > 0:
                yield hazard.id, assets, data

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
    def __call__(self, monitor=None):
        """
        Override base method to seed the rng for each hazard output
        """
        for hazard, seed in zip(self.hazard_outputs, self.seeds):
            h = hazard.output_container
            numpy.random.seed(seed)
            assets, data = self.get_assets_data(h, monitor)
            if len(assets) > 0:
                yield hazard.id, assets, data

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
