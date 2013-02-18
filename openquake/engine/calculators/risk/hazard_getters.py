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


DEFAULT_MAXIMUM_DISTANCE = 50000


class HazardGetter(object):
    def __init__(self, hazard_id, imt, assets,
                 max_distance=DEFAULT_MAXIMUM_DISTANCE):
        self.hazard_id = hazard_id
        self.imt = imt
        self.assets = assets
        self.max_distance = max_distance
        self._assets_extent = None  # A polygon that includes all the assets

        # IMT exploded in three variables
        self._imt = None
        self._sa_period = None
        self._sa_damping = None

        self.setup()

    def setup(self):
        self._assets_extent = geo.mesh.Mesh.from_points_list([
            geo.point.Point(asset.site.x, asset.site.y)
            for asset in self.assets]).get_convex_hull()
        self._imt, self._sa_period, self._sa_damping = (
            models.parse_imt(self.imt))

    def __call__(self):
        raise NotImplementedError

    def __getstate__(self):
        return (self.hazard_id, self.imt, self.assets, self.max_distance)

    def __setstate__(self, params):
        self.hazard_id = params[0]
        self.imt = params[1]
        self.assets = params[2]
        self.max_distance = params[3]
        self.setup()


class HazardCurveGetterPerAsset(HazardGetter):
    """
    Simple HazardCurve Getter that performs a query per asset.

    It caches the computed hazard curve object on a per-location basis.
    """

    # FIXME(lp). There is a room for optimization here.... A possible
    # solution is to use the same approach used in GmfValuesGetter

    def __init__(self, hazard_id, imt, assets,
                 max_distance=DEFAULT_MAXIMUM_DISTANCE):
        super(HazardCurveGetterPerAsset, self).__init__(
            hazard_id, imt, assets, max_distance)

        self.imls = None
        self._cache = None

    def setup(self):
        super(HazardCurveGetterPerAsset, self).setup()
        self.imls = models.HazardCurve.objects.get(
            pk=self.hazard_id).imls
        self._cache = {}

    def __call__(self):
        """
        :returns: a list of poEs for each asset.
        :params assets: an interable over point objects
        """
        return [self.get_by_site(asset.site) for asset in self.assets]

    def get_by_site(self, site):
        """
        :param location:
            `django.contrib.gis.geos.point.Point` object.
        """
        if site.wkt in self._cache:
            return self._cache[site.wkt]

        cursor = connection.cursor()

        query = """
        SELECT
            hzrdr.hazard_curve_data.poes,
            min(ST_Distance_Sphere(location, %s))
                AS min_distance
        FROM hzrdr.hazard_curve_data
        WHERE hazard_curve_id = %s
        GROUP BY id
        ORDER BY min_distance
        LIMIT 1;"""

        args = ('SRID=4326; %s' % site.wkt, self.hazard_id)

        cursor.execute(query, args)
        poes = cursor.fetchone()[0]

        hazard = zip(self.imls, poes)

        self._cache[site.wkt] = hazard

        return hazard


class GroundMotionValuesGetter(HazardGetter):
    """
    Hazard getter for loading ground motion values.
    It caches the ground motion values on a per-location basis.

    :param int hazard_output_id:
        Id of the hazard output (`openquake.engine.db.models.Output`) used to
        look up the ground motion values. This implementation only supports
        plain `gmf` output types (single logic tree branch or realization).
    :param str imt:
        The intensity measure type with which the ground motion
        values have been computed (long form).

    """

    def _load_gmf_set_ids(self):
        """
        At the moment, we only support risk calculations using ground motion
        fields coming from a specific realization.
        """
        gmf_collection = models.GmfCollection.objects.get(
            id=self.hazard_id)

        if gmf_collection.output.output_type == "gmf":
            return tuple(
                gmf_collection.gmfset_set.values_list('id', flat=True))
        else:
            raise ValueError(
                "Output must be of type `gmf`. "
                "At the moment, we only support computation of loss curves "
                "for a specific logic tree branch.")

    def __call__(self):
        cursor = connection.cursor()

        spectral_filters = ""
        args = (self._imt, self._load_gmf_set_ids())

        if self._imt == "SA":
            spectral_filters = "AND sa_period = %s AND sa_damping = %s"
            args += (self._sa_period, self._sa_damping)

        query = """
  SELECT DISTINCT ON (oqmif.exposure_data.id)
  oqmif.exposure_data.id, ST_AsText(location), gmf_table.allgmvs_arr
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
  ORDER BY oqmif.exposure_data.id,
           ST_Distance(oqmif.exposure_data.site, gmf_table.location)
           """.format(spectral_filters)  # this will fill in the {}

        args += (self._assets_extent.dilate(self.max_distance / 1000).wkt,
                 self.max_distance,
                 self._assets_extent.wkt,
                 self.assets[0].taxonomy,
                 self.assets[0].exposure_model_id)

        cursor.execute(query, args)

        data = cursor.fetchall()
        gmvs = OrderedDict((row[0], row[2]) for row in data)

        if len(gmvs) > len(self.assets):
            logs.LOG.error(
                "More assets %s returned than requested %s",
                gmvs.keys(), self.assets)
            raise RuntimeError("More assets returned than requested")
        elif len(gmvs) < len(self.assets):
            for asset in self.assets:
                if not asset.id in gmvs.keys():
                    logs.LOG.warn(
                        "Asset %s has no hazard within a distance of %s m",
                        asset, self.max_distance)
        else:
            for asset_id, location, _gmvs in data:
                logs.LOG.debug(
                    "Asset with id %s got the hazard in location %s",
                    asset_id, location)

        return gmvs.values()


class GroundMotionScenarioGetter(HazardGetter):
    """
    Hazard getter for loading ground motion values from the table
    gmf_scenario.
    It caches the ground motion values on a per-location basis.

    :param int hazard_id:
        Id of the hazard output (`openquake.engine.db.models.Output`) used to
        look up the ground motion values. This implementation only supports
        plain `gmf` output types (single logic tree branch or realization).
    :param str imt:
        The intensity measure type with which the ground motion
        values have been computed (long form).
    """

    def setup(self):
        super(GroundMotionScenarioGetter, self).setup()
        self._cache = {}

    def __call__(self):
        return [self.get_per_site(a.site) for a in self.assets]

    def get_per_site(self, site):
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
        SELECT min(ST_Distance(location, %s)) FROM hzrdr.gmf_scenario
        WHERE imt = %s AND output_id = %s {}""".format(
            spectral_filters)

        cursor.execute(min_dist_query, args)
        min_dist = cursor.fetchall()[0][0]  # returns only one row
        if min_dist is None:
            raise RuntimeError(
                'Could not find any gmf with IMT=%s '
                'and output_id=%s' % (self._imt, self._hazard_output_id))

        min_dist = min_dist + 0.1  # 0.1 meters = 10 cm

        gmvs_query = """-- return all the gmvs inside the min_dist radius
        SELECT gmvs FROM hzrdr.gmf_scenario
        WHERE %s > ST_Distance(location, %s)
        AND imt = %s AND output_id = %s {}
        ORDER BY result_grp_ordinal
        """.format(spectral_filters)

        cursor.execute(gmvs_query, (min_dist,) + args)

        ground_motion_values = sum([row[0] for row in cursor], [])
        self._cache[site.wkt] = ground_motion_values
        return ground_motion_values


class GroundMotionScenarioGetter2(HazardGetter):
    """
    Hazard getter for loading ground motion values.
    It uses the same approach used in GroundMotionValuesGetter
    """

    def __call__(self):
        cursor = connection.cursor()

        spectral_filters = ""
        args = (self.max_distance, self._imt, self.hazard_id)

        if self._imt == "SA":
            spectral_filters = "AND sa_period = %s AND sa_damping = %s"
            args += (self._sa_period, self._sa_damping)

        query = """
  SELECT DISTINCT ON (oqmif.exposure_data.id)
  oqmif.exposure_data.id, ST_AsText(location), gmvs
  FROM oqmif.exposure_data JOIN hzrdr.gmf_scenario
  ON ST_DWithin(oqmif.exposure_data.site, gmf_scenario.location, %s)
  WHERE hzrdr.gmf_scenario.imt = %s AND hzrdr.gmf_scenario.output_id = %s {}
    AND hzrdr.gmf_scenario.location && %s
    AND oqmif.exposure_data.site && %s
    AND taxonomy = %s AND exposure_model_id = %s
  ORDER BY oqmif.exposure_data.id,
           ST_Distance(oqmif.exposure_data.site, hzrdr.gmf_scenario.location)
           """.format(spectral_filters)  # this will fill in the {}

        args += (self._assets_extent.dilate(self.max_distance / 1000).wkt,
                 self._assets_extent.wkt,
                 self.assets[0].taxonomy,
                 self.assets[0].exposure_model_id)

        cursor.execute(query, args)

        data = cursor.fetchall()
        gmvs = OrderedDict((row[0], row[2]) for row in data)

        if len(gmvs) > len(self.assets):
            logs.LOG.error(
                "More assets %s returned than requested %s",
                gmvs.keys(), self.assets)
            raise RuntimeError("More assets returned than requested")
        elif len(gmvs) < len(self.assets):
            for asset in self.assets:
                if not asset.id in gmvs.keys():
                    logs.LOG.warn(
                        "Asset %s has no hazard within a distance of %s m",
                        asset, self.max_distance)
        else:
            for asset_id, location, _gmvs in data:
                logs.LOG.debug(
                    "Asset with id %s got the hazard in location %s",
                    asset_id, location)

        return gmvs.values()
