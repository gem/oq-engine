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

from collections import OrderedDict
from openquake.engine import logs
from openquake.hazardlib import geo
from openquake.engine.db import models
from django.db import connections


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

    :attr hazard_id:
        The ID of an Hazard output container (e.g.
        :class:`openquake.engine.db.models.HazardCurve`)

    :attr imt:
        The imt of the hazard considered by the getter.

    :attr assets:
        The assets for which we wants to compute.

    :attr max_distance:
        The maximum distance, in kilometers, to use.
    """
    def __init__(self, hazard_id, imt, assets, max_distance):
        self.hazard_id = hazard_id
        self.imt = imt
        self.assets = assets
        self.max_distance = max_distance

        self._assets_mesh = geo.mesh.Mesh.from_points_list([
            geo.point.Point(asset.site.x, asset.site.y)
            for asset in self.assets])
        self._imt, self._sa_period, self._sa_damping = (
            models.parse_imt(self.imt))
        self.asset_dict = dict((asset.id, asset) for asset in self.assets)

        self._cache = {}

    def __repr__(self):
        return """HazardGetter imt=%s max_distance=%s assets=%s""" % (
            self.imt, self.max_distance, self.assets)

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
            A tuple with three elements. The first is an array of instances of
            :class:`openquake.engine.db.models.ExposureData`, the second is an
            array with the corresponding hazard data, the third is the array of
            IDs of assets that has been filtered out by the getter by the
            ``maximum_distance`` criteria.
        """
        data = self.get_data()

        filtered_asset_ids = set(data.keys())
        all_asset_ids = set(self.asset_dict.keys())
        missing_asset_ids = all_asset_ids - filtered_asset_ids
        extra_asset_ids = filtered_asset_ids - all_asset_ids

        # FIXME(lp). It might happens that the convex hull contains
        # more assets than the requested ones. At this moment, we just
        # ignore them.
        if extra_asset_ids:
            logs.LOG.debug("Extra asset have been computed ids: %s" % (
                models.ExposureData.objects.filter(
                    pk__in=extra_asset_ids)))

        for missing_asset_id in missing_asset_ids:
            logs.LOG.warn(
                "No hazard has been found for the asset %s within %s km" % (
                    self.asset_dict[missing_asset_id], self.max_distance))

        return ([self.asset_dict[asset_id] for asset_id in data
                 if asset_id in self.asset_dict],
                [data[asset_id] for asset_id in data
                 if asset_id in self.asset_dict],
                missing_asset_ids)


class HazardCurveGetterPerAsset(HazardGetter):
    """
    Simple HazardCurve Getter that performs a spatial query for each
    asset.

    :attr imls:
        The intensity measure levels of the curves we are going to get.

    :attr dict _cache:
        A cache of the computed hazard curve object on a per-location basis.
    """

    def __init__(self, hazard_id, imt, assets, max_distance):
        super(HazardCurveGetterPerAsset, self).__init__(
            hazard_id, imt, assets, max_distance)
        self.imls = models.HazardCurve.objects.get(
            pk=self.hazard_id).imls

    def get_data(self):
        """
        Calls ``get_by_site`` for each asset and pack the results as requested
        by the :meth:`HazardGetter.get_data` interface.
        """
        hazard_assets = [(asset.id, self.get_by_site(asset.site))
                         for asset in self.assets]

        return OrderedDict(
            [(asset_id, hazard_curve)
             for asset_id, (hazard_curve, distance) in hazard_assets
             if distance < self.max_distance * KILOMETERS_TO_METERS])

    def get_by_site(self, site):
        """
        :param site:
            An instance of :class:`django.contrib.gis.geos.point.Point`
            corresponding to the location of an asset.
        """
        if site.wkt in self._cache:
            return self._cache[site.wkt]

        cursor = connections['job_init'].cursor()

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

        args = (site.wkt, self.hazard_id)

        cursor.execute(query, args)
        poes, distance = cursor.fetchone()

        hazard = zip(self.imls, poes)

        self._cache[site.wkt] = (hazard, distance)

        return hazard, distance


class GroundMotionValuesGetter(HazardGetter):
    """
    Hazard getter for loading ground motion values.
    """

    def get_data(self):
        gmf_collection = models.GmfCollection.objects.get(
            id=self.hazard_id)

        if gmf_collection.output.output_type != "gmf":
            raise ValueError(
                "Output must be of type `gmf`. "
                "At the moment, we only support computation of loss curves "
                "for a specific logic tree branch.")

        cursor = connections['job_init'].cursor()

        spectral_filters = ""
        args = (self._imt, gmf_collection.id)

        if self._imt == "SA":
            spectral_filters = "AND sa_period = %s AND sa_damping = %s"
            args += (self._sa_period, self._sa_damping)

        # Query explanation. We need to get for each asset the closest
        # ground motion values (and the corresponding rupture ids from
        # which they have been generated) for a given logic tree
        # realization and a given imt.

        # We first concatenate ground motion values grouped by
        # location (so for each location we have all the ground motion
        # values found in different gmf_sets, collected in a column
        # called ``allgmvs_arr``).

        # For performance reasons, we help the query by filtering also
        # on a polygon built by dilating the assets extent of the
        # maximum distance

        # Then, we perform a spatial join with the exposure table that
        # is previously filtered by the assets extent, exposure model
        # and taxonomy. We are not filtering with an IN statement on
        # the ids of the assets for perfomance reasons.

        # The ``distinct ON (exposure_data.id)`` combined by the
        # ``ORDER BY ST_Distance`` does the job to select the closest
        # gmvs
        query = """
  SELECT DISTINCT ON (oqmif.exposure_data.id)
  oqmif.exposure_data.id, gmf_table.gmvs, gmf_table.rupture_ids
  FROM oqmif.exposure_data JOIN
  (SELECT * FROM hzrdr.gmf_agg
  WHERE imt = %s AND gmf_collection_id = %s {} AND location && %s) AS gmf_table
  ON ST_DWithin(oqmif.exposure_data.site, gmf_table.location, %s)
  WHERE oqmif.exposure_data.site && %s
  AND taxonomy = %s AND exposure_model_id = %s
  AND array_length(gmf_table.gmvs, 1) > 0
  ORDER BY oqmif.exposure_data.id,
           ST_Distance(oqmif.exposure_data.site, gmf_table.location, false)
           """.format(spectral_filters)  # this will fill in the {}

        assets_extent = self._assets_mesh.get_convex_hull()
        args += (assets_extent.dilate(self.max_distance).wkt,
                 self.max_distance * KILOMETERS_TO_METERS,
                 assets_extent.wkt,
                 self.assets[0].taxonomy,
                 self.assets[0].exposure_model_id)

        cursor.execute(query, args)

        data = cursor.fetchall()

        # nested dicts with structure: asset_id -> (rupture_id -> gmv)
        assets_ruptures_gmvs = OrderedDict()

        # store all the ruptures returned by the query
        ruptures = []

        for asset_id, gmvs, rupture_ids in data:
            assets_ruptures_gmvs[asset_id] = dict(zip(rupture_ids, gmvs))
            ruptures.extend(rupture_ids)
        ruptures = set(ruptures)

        # We expect that the query may return a different number of
        # gmvs and ruptures for each asset (because only the ruptures
        # that gives a positive ground shaking are stored). Here on,
        # we finalize `assets_ruptures_gmvs` by filling in with zero
        # values for each rupture that has not given a contribute.

        # for each asset, we look for missing ruptures
        for asset_id, ruptures_gmvs_dict in assets_ruptures_gmvs.items():

            # all the ruptures producing a positive ground shaking for
            # `asset`
            asset_ruptures = set(ruptures_gmvs_dict)

            missing_ruptures = ruptures - asset_ruptures

            # we finalize the asset data with 0
            for rupture_id in missing_ruptures:
                ruptures_gmvs_dict[rupture_id] = 0.

        # maps asset_id -> to a 2-tuple (rupture_ids, gmvs)
        return OrderedDict([
            (asset_id, zip(
                *sorted(zip(asset_data.values(), asset_data.keys()),
                        key=lambda x: x[1])))
            for asset_id, asset_data in assets_ruptures_gmvs.items()])


class GroundMotionScenarioGetter(HazardGetter):
    """
    Hazard getter for loading ground motion values. It uses the same
    approach used in :class:`GroundMotionValuesGetter`.
    """

    def get_data(self):
        cursor = connections['job_init'].cursor()

        # See the comment in `GroundMotionValuesGetter.get_data` for
        # an explanation of the query
        query = """
  SELECT DISTINCT ON (oqmif.exposure_data.id) oqmif.exposure_data.id,
         gmf_table.gmvs
  FROM oqmif.exposure_data JOIN (
    SELECT location, gmvs
           FROM hzrdr.gmf_scenario
           WHERE hzrdr.gmf_scenario.imt = %s
           AND hzrdr.gmf_scenario.output_id = %s
           AND hzrdr.gmf_scenario.location && %s) gmf_table
  ON ST_DWithin(oqmif.exposure_data.site, gmf_table.location, %s)
  WHERE oqmif.exposure_data.site && %s
    AND taxonomy = %s AND exposure_model_id = %s
  ORDER BY oqmif.exposure_data.id,
    ST_Distance(oqmif.exposure_data.site, gmf_table.location, false)
           """

        imt = self._imt
        if self._sa_period is not None:
            imt = '%s(%s)' % (imt, self._sa_period)

        assets_extent = self._assets_mesh.get_convex_hull()
        args = (imt, self.hazard_id,
                assets_extent.dilate(self.max_distance).wkt,
                self.max_distance * KILOMETERS_TO_METERS,
                assets_extent.wkt,
                self.assets[0].taxonomy,
                self.assets[0].exposure_model_id)
        cursor.execute(query, args)

        return OrderedDict(cursor.fetchall())
