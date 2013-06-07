# -*- coding: utf-8 -*-

# Copyright (c) 2010-2013, GEM Foundation.
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

import numpy

from openquake.engine import logs
from openquake.hazardlib import geo
from openquake.engine.db import models
from openquake.engine.performance import DummyMonitor

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

    :attr int hazard_output:
        A Hazard Output object :class:`openquake.engine.db.models.Output`

    :attr int hazard_id:
        The ID of an Hazard Output container object
        (e.g. :class:`openquake.engine.db.models.HazardCurve`)

    :attr assets:
        The assets for which we wants to compute.

    :attr max_distance:
        The maximum distance, in kilometers, to use.

    :attr imt:
        The imt (in long form) for which data have to be retrieved

    :attr float weight:
        The weight (if applicable) to be given to the retrieved data
    """
    def __init__(self, hazard_output, assets, max_distance, imt):
        self.hazard_output = hazard_output
        hazard = hazard_output.output_container
        self.hazard_id = hazard.id
        self.assets = assets
        self.max_distance = max_distance
        self.imt = imt
        self.imt_type, self.sa_period, self.sa_damping = models.parse_imt(imt)
        if hasattr(hazard, 'lt_realization') and hazard.lt_realization:
            self.weight = hazard.lt_realization.weight
        else:
            self.weight = None
        # FIXME(lp). It is better to directly store the convex hull
        # instead of the mesh. We are not doing it because
        # hazardlib.Polygon is not (yet) pickeable
        self._assets_mesh = geo.mesh.Mesh.from_points_list([
            geo.point.Point(asset.site.x, asset.site.y)
            for asset in self.assets])
        self.asset_dict = dict((asset.id, asset) for asset in self.assets)
        self.all_asset_ids = set(self.asset_dict)

    def __repr__(self):
        return "<%s max_distance=%s assets=%s>" % (
            self.__class__.__name__, self.max_distance,
            [a.id for a in self.assets])

    def get_data(self):
        """
        Subclasses must implement this.

        :returns:
            An OrderedDict mapping ID of
            :class:`openquake.engine.db.models.ExposureData` objects to
            hazard_data (e.g. an array with the poes, or an array with the
            ground motion values). Bear in mind that the returned data could
            lack some assets being filtered out by the ``maximum_distance``
            criteria.
        """
        raise NotImplementedError

    def __call__(self):
        """
        :returns:
            A tuple with two elements. The first is an array of instances of
            :class:`openquake.engine.db.models.ExposureData`, the second is an
            array with the corresponding hazard data.
        """
        # data is a pair (gmvs, ruptures) or a set of hazard curves
        assets, data = self.get_data()

        missing_asset_ids = self.all_asset_ids - set(a.id for a in assets)

        for missing_asset_id in missing_asset_ids:
            # please don't remove this log: it was required by Vitor since
            # this is a case that should NOT happen and must raise a warning
            logs.LOG.warn(
                "No hazard has been found for the asset %s within %s km" % (
                    self.asset_dict[missing_asset_id], self.max_distance))

        return assets, data


class HazardCurveGetterPerAsset(HazardGetter):
    """
    Simple HazardCurve Getter that performs a spatial query for each
    asset.

    :attr imls:
        The intensity measure levels of the curves we are going to get.

    :attr dict _cache:
        A cache of the computed hazard curve object on a per-location basis.
    """

    def __init__(self, hazard, assets, max_distance, imt):
        super(HazardCurveGetterPerAsset, self).__init__(
            hazard, assets, max_distance, imt)
        self._cache = {}

    def get_data(self):
        """
        Calls ``get_by_site`` for each asset and pack the results as
        requested by the :meth:`HazardGetter.get_data` interface.
        """
        hc = models.HazardCurve.objects.get(pk=self.hazard_id)

        if hc.output.output_type == 'hazard_curve':
            imls = hc.imls
            hazard_id = self.hazard_id
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
            hazard_id = hc.id

        hazard_assets = [
            (asset.id, self.get_by_site(asset.site, hazard_id, imls))
            for asset in self.assets]

        assets = []
        curves = []
        for asset_id, (hazard_curve, distance) in hazard_assets:
            if distance < self.max_distance * KILOMETERS_TO_METERS:
                assets.append(self.asset_dict[asset_id])
                curves.append(hazard_curve)

        return assets, curves

    def get_by_site(self, site, hazard_id, imls):
        """
        :param site:
            An instance of :class:`django.contrib.gis.geos.point.Point`
            corresponding to the location of an asset.
        """
        if site.wkt in self._cache:
            return self._cache[site.wkt]

        cursor = models.getcursor('job_init')

        query = """
        SELECT
            hzrdr.hazard_curve_data.poes,
            min(ST_Distance(location::geography,
                            ST_GeographyFromText(%s), false))
                AS min_distance
        FROM hzrdr.hazard_curve_data
        WHERE hazard_curve_id = %s
        GROUP BY id
        ORDER BY min_distance
        LIMIT 1;"""

        args = (site.wkt, hazard_id)

        cursor.execute(query, args)
        poes, distance = cursor.fetchone()

        hazard = zip(imls, poes)

        self._cache[site.wkt] = (hazard, distance)

        return hazard, distance


class GroundMotionValuesGetter(HazardGetter):
    """
    Hazard getter for loading ground motion values. It is instantiated
    with a set of assets all of the same taxonomy.
    """
    def __init__(self, hazard_output, assets, max_distance, imt):
        super(GroundMotionValuesGetter, self).__init__(
            hazard_output, assets, max_distance, imt)

    def __iter__(self):
        """
        Iterator yielding site_id, assets.
        """
        cursor = models.getcursor('job_init')
        # NB: the ``distinct ON (exposure_data.id)`` combined by the
        # ``ORDER BY ST_Distance`` does the job to select the closest site
        query = """
SELECT site_id, array_agg(asset_id) AS asset_ids FROM (
  SELECT DISTINCT ON (exp.id) exp.id AS asset_id, hsite.id AS site_id
  FROM riski.exposure_data AS exp
  JOIN hzrdi.hazard_site AS hsite
  ON ST_DWithin(exp.site, hsite.location, %s)
  WHERE hsite.hazard_calculation_id = %s
  AND taxonomy = %s AND exposure_model_id = %s AND exp.site && %s
  ORDER BY exp.id, ST_Distance(exp.site, hsite.location, false)) AS x
GROUP BY site_id;
   """
        args = (self.max_distance * KILOMETERS_TO_METERS,
                self.hazard_output.oq_job.hazard_calculation.id,
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
            if assets:
                yield site_id, assets

    def get_gmvs_ruptures(self, site_id):
        """
        :returns: gmvs and ruptures for the given site and IMT
        """
        gmvs = []
        ruptures = []
        for gmf in models.GmfAgg.objects.filter(
                gmf_collection=self.hazard_output.gmf.id,
                site=site_id, imt=self.imt_type, sa_period=self.sa_period,
                sa_damping=self.sa_damping):
            gmvs.extend(gmf.gmvs)
            if gmf.rupture_ids:
                ruptures.extend(gmf.rupture_ids)
        if not gmvs:
            logs.LOG.warn('No gmvs for site %s, IMT=%s', site_id, self.imt)
        return gmvs, ruptures

    def get_data(self):
        all_assets = []
        all_gmvs_ruptures = []
        for site_id, assets in self:
            all_assets.extend(assets)
            gmvs, ruptures = self.get_gmvs_ruptures(site_id)
            all_gmvs_ruptures.extend([(gmvs, ruptures)] * len(assets))
        return all_assets, all_gmvs_ruptures
