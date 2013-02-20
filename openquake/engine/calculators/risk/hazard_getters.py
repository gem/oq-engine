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

An HazardGetter is responsible to get hazard outputs needed by a risk
calculation.
"""

from collections import OrderedDict
from openquake.engine import logs
from openquake.hazardlib import geo
from openquake.engine.db import models
from django.db import connection


class HazardGetter(object):
    """
    Base abstract class of an Hazard Getter.

    An Hazard Getter is used to query for the closest hazard data for
    each given asset. An Hazard Getter must be pickable such that it
    should be possible to use different strategies (e.g. distributed
    or not, using postgis or not).

    :attr hazard_id:
      the ID of an Hazard output container (e.g.
      :class:`openquake.engine.db.models.HazardCurve`)

    :attr imt: the imt of the hazard considered by the getter

    :attr assets: the assets for which we wants to compute

    :attr max_distance: the maximum distance, in meters, to use
    """
    def __init__(self, hazard_id, imt, assets, max_distance):
        self.hazard_id = hazard_id
        self.imt = imt
        self.assets = assets
        self.max_distance = max_distance
        self._assets_extent = None  # A polygon that includes all the assets

        # IMT exploded in three variables
        self._imt = None
        self._sa_period = None
        self._sa_damping = None

        # a dictionary mapping ID -> Asset
        self.asset_dict = None

        self.setup()

    def setup(self):
        """
        Initialize private variables of an hazard getter. Called by
        ``__init__`` and by ``__setstate``.
        """
        self._assets_extent = geo.mesh.Mesh.from_points_list([
            geo.point.Point(asset.site.x, asset.site.y)
            for asset in self.assets]).get_convex_hull()
        self._imt, self._sa_period, self._sa_damping = (
            models.parse_imt(self.imt))
        self.asset_dict = dict((asset.id, asset) for asset in self.assets)

    def get_data(self):
        """
        :returns: an array of the form ``[[asset_id, hazard_data],
        [asset_id, hazard_data], ...]``, where each element is an
        array with the first element being the asset_id and the second
        element the hazard data (e.g. an array with the poes, or an
        array with the ground motion values). Mind that the returned
        data could lack some assets being filtered out by the
        ``maximum_distance`` criteria.

        Subclasses must implement this.
        """
        raise NotImplementedError

    def __call__(self):
        """
        :returns: a tuple with three elements. The first is an array
        of instances of
        :class:`openquake.engine.db.models.ExposureData`, the second
        is an array with the corresponding hazard data, the third is
        the array of IDs of assets that has been filtered out by the
        getter by the ``maximum_distance`` criteria.
        """
        data = OrderedDict(self.get_data())

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
                "No hazard has been found for the asset %s",
                self.asset_dict[missing_asset_id].asset_ref)

        return ([self.asset_dict[asset_id] for asset_id in data
                 if asset_id in self.asset_dict],
                [data[asset_id] for asset_id in data
                 if asset_id in self.asset_dict],
                missing_asset_ids)

    def __getstate__(self):
        """Implements the pickable protocol"""
        return (self.hazard_id, self.imt, self.assets, self.max_distance)

    def __setstate__(self, params):
        """Implements the pickable protocol. Calls the ``setup``
        method."""
        self.hazard_id = params[0]
        self.imt = params[1]
        self.assets = params[2]
        self.max_distance = params[3]
        self.setup()


class HazardCurveGetterPerAsset(HazardGetter):
    """
    Simple HazardCurve Getter that performs a spatial query for each
    asset.

    :attr imls: the intensity measure levels of the curves we are
    going to get. We just fetch it in the ``setup`` phase.

    :attr dict _cache: a cache of the computed hazard curve object on
    a per-location basis.
    """

    def __init__(self, hazard_id, imt, assets, max_distance):
        super(HazardCurveGetterPerAsset, self).__init__(
            hazard_id, imt, assets, max_distance)

        self.imls = None
        self._cache = {}
        self.setup()

    def setup(self):
        super(HazardCurveGetterPerAsset, self).setup()
        self.imls = models.HazardCurve.objects.get(
            pk=self.hazard_id).imls
        self._cache = {}

    def get_data(self):
        """
        Calls ``get_by_site`` for each asset and pack the results as
        requested by the :method:`HazardGetter.get_data` interface.
        """
        return [(data[0], data[1][0]) for data in
                [(asset.id, self.get_by_site(asset.site))
                 for asset in self.assets]
                if data[1][1] < self.max_distance]

    def get_by_site(self, site):
        """
        :param site: an instance of
        :class:`django.contrib.gis.geos.point.Point` corresponding to
        the location of an asset.
        """
        if site.wkt in self._cache:
            return self._cache[site.wkt]

        cursor = connection.cursor()

        query = """
        SELECT
            hzrdr.hazard_curve_data.poes,
            min(ST_Distance(location, %s, false))
                AS min_distance
        FROM hzrdr.hazard_curve_data
        WHERE hazard_curve_id = %s
        GROUP BY id
        ORDER BY min_distance
        LIMIT 1;"""

        args = ('SRID=4326; %s' % site.wkt, self.hazard_id)

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

        if gmf_collection.output.output_type == "gmf":
            gmf_set_ids = tuple(
                gmf_collection.gmfset_set.values_list('id', flat=True))
        else:
            raise ValueError(
                "Output must be of type `gmf`. "
                "At the moment, we only support computation of loss curves "
                "for a specific logic tree branch.")

        cursor = connection.cursor()

        spectral_filters = ""
        args = (self._imt, gmf_set_ids)

        if self._imt == "SA":
            spectral_filters = "AND sa_period = %s AND sa_damping = %s"
            args += (self._sa_period, self._sa_damping)

        # Query explanation. We need to get for each asset the closest
        # ground motion values for a given logic tree realization and
        # a given imt.

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
  oqmif.exposure_data.id, gmf_table.allgmvs_arr
  FROM oqmif.exposure_data JOIN
    (SELECT location,
            array_concat(gmvs ORDER BY gmf_set_id, result_grp_ordinal)
     AS allgmvs_arr FROM hzrdr.gmf
     WHERE imt = %s AND gmf_set_id IN %s {}
     AND location && %s
     GROUP BY location) AS gmf_table
  ON ST_DWithin(oqmif.exposure_data.site, gmf_table.location, %s)
  WHERE oqmif.exposure_data.site && %s
  AND taxonomy = %s AND exposure_model_id = %s
  AND array_length(gmf_table.allgmvs_arr, 1) > 0
  ORDER BY oqmif.exposure_data.id,
           ST_Distance(oqmif.exposure_data.site, gmf_table.location, false)
           """.format(spectral_filters)  # this will fill in the {}

        args += (self._assets_extent.dilate(self.max_distance / 1000).wkt,
                 self.max_distance,
                 self._assets_extent.wkt,
                 self.assets[0].taxonomy,
                 self.assets[0].exposure_model_id)

        cursor.execute(query, args)

        return cursor.fetchall()


class GroundMotionScenarioGetterPerAsset(HazardGetter):
    """
    Hazard getter for loading ground motion values from the table
    gmf_scenario. It performs two spatial queries per asset.

    :attr _cache: a cache of the ground motion values on a
    per-location basis
    """

    def setup(self):
        super(GroundMotionScenarioGetterPerAsset, self).setup()
        self._cache = {}

    def get_data(self):
        return [(data[0], data[1][0]) for data in
                [(asset.id, self.get_by_site(asset.site))
                 for asset in self.assets]
                if data[1][1] < self.max_distance]

    def get_by_site(self, site):
        """
        Return the closest ground motion values to the given location.

        :param site:
            The reference location. The closest ground motion values
            to this location are returned.
        :type site: `django.contrib.gis.geos.point.Point` object
        """

        if site.wkt in self._cache:
            return self._cache[site.wkt]

        cursor = connection.cursor()

        spectral_filters = ""
        args = ("SRID=4326; %s" % site.wkt, self._imt, self.hazard_id)

        if self._imt == "SA":
            spectral_filters = "AND sa_period = %s AND sa_damping = %s"
            args += (self._sa_period, self._sa_damping)

        min_dist_query = """-- find the distance of the closest location
        SELECT min(ST_Distance(location, %s, false)) FROM hzrdr.gmf_scenario
        WHERE imt = %s AND output_id = %s {}""".format(
            spectral_filters)

        cursor.execute(min_dist_query, args)
        min_dist = cursor.fetchall()[0][0]  # returns only one row
        if min_dist is None:
            raise RuntimeError(
                'Could not find any gmf with IMT=%s '
                'and output_id=%s' % (self._imt, self._hazard_output_id))

        dilated_dist = min_dist + 0.1  # 0.1 meters = 10 cm

        gmvs_query = """-- return all the gmvs inside the min_dist radius
        SELECT gmvs FROM hzrdr.gmf_scenario
        WHERE %s > ST_Distance(location, %s, false)
        AND imt = %s AND output_id = %s {}
        ORDER BY result_grp_ordinal
        """.format(spectral_filters)

        cursor.execute(gmvs_query, (dilated_dist,) + args)

        ground_motion_values = sum([row[0] for row in cursor], [])
        self._cache[site.wkt] = ground_motion_values
        return ground_motion_values, min_dist


class GroundMotionScenarioGetter(HazardGetter):
    """
    Hazard getter for loading ground motion values. It uses the same
    approach used in :class:`GroundMotionValuesGetter`.
    """

    def get_data(self):
        cursor = connection.cursor()

        spectral_filters = ""
        args = (self._imt, self.hazard_id)

        if self._imt == "SA":
            spectral_filters = "AND sa_period = %s AND sa_damping = %s"
            args += (self._sa_period, self._sa_damping)

        # See the comment in `GroundMotionValuesGetter.get_data` for
        # an explanation of the query
        query = """
  SELECT DISTINCT ON (oqmif.exposure_data.id) oqmif.exposure_data.id,
         gmf_table.allgmvs
  FROM oqmif.exposure_data JOIN (
    SELECT location, array_concat(gmvs ORDER BY result_grp_ordinal) as allgmvs
           FROM hzrdr.gmf_scenario
           WHERE hzrdr.gmf_scenario.imt = %s
           AND hzrdr.gmf_scenario.output_id = %s {}
           AND hzrdr.gmf_scenario.location && %s
           GROUP BY location) gmf_table
  ON ST_DWithin(oqmif.exposure_data.site, gmf_table.location, %s)
  WHERE oqmif.exposure_data.site && %s
    AND taxonomy = %s AND exposure_model_id = %s
    AND array_length(gmf_table.allgmvs, 1) > 0
  ORDER BY oqmif.exposure_data.id,
    ST_Distance(oqmif.exposure_data.site, gmf_table.location, false)
           """.format(spectral_filters)  # this will fill in the {}

        args += (self._assets_extent.dilate(self.max_distance / 1000).wkt,
                 self.max_distance,
                 self._assets_extent.wkt,
                 self.assets[0].taxonomy,
                 self.assets[0].exposure_model_id)

        cursor.execute(query, args)

        return cursor.fetchall()
