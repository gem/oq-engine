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

from openquake.db import models
from django.db import connection


class HazardCurveGetterPerAsset(object):
    """
    Simple HazardCurve Getter that performs a query per asset.

    It caches the computed hazard curve object on a per-location basis.
    """
    def __init__(self, hazard_curve_id):
        self.hazard_curve_id = hazard_curve_id
        self.imls = models.HazardCurve.objects.get(pk=hazard_curve_id).imls
        self._cache = {}

    def __call__(self, site):
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

        args = ('SRID=4326; %s' % site.wkt, self.hazard_curve_id)

        cursor.execute(query, args)
        poes = cursor.fetchone()[0]

        hazard = zip(self.imls, poes)

        self._cache[site.wkt] = hazard

        return hazard


# Note on the algorithm: the idea is to first compute the minimal distance
# between the given site and the ground motion fields in the mesh; then the
# ground motion values are extracted from the points at that distance. To
# cope with numerical errors we extract all the ground motion fields within
# the minimal distance plus 10 centimers (any "small" number would do).
# This is ~6 times faster than using a group by/order by to extract the
# locations/gmvs directly with a single query.
def _get_min_distance(self, cursor, min_dist_query, args):
    # no docstring on purpose: private functions should not have it
    cursor.execute(min_dist_query, args)
    min_dist = cursor.fetchall()[0][0]  # returns only one row
    if min_dist is None:
        raise RuntimeError(
            'Could not find any gmf_scenarios for IMT=%s '
            'and output_id=%s' % (self._imt, self._hazard_output_id))

    return min_dist + 0.1  # 0.1 meters = 10 cm


class GroundMotionValuesGetter(object):
    """
    Hazard getter for loading ground motion values.
    It caches the ground motion values on a per-location basis.

    :param int hazard_output_id:
        Id of the hazard output (`openquake.db.models.Output`) used to
        look up the ground motion values. This implementation only supports
        plain `gmf` output types (single logic tree branch or realization).
    :param str imt:
        The intensity measure type with which the ground motion
        values have been computed (long form).

    """

    def __init__(self, hazard_output_id, imt):
        imt, sa_period, sa_damping = models.parse_imt(imt)

        self._imt = imt
        self._sa_period = sa_period
        self._sa_damping = sa_damping
        self._hazard_output_id = hazard_output_id

        self._cache = {}

        self._gmf_set_ids = self._load_gmf_set_ids()

    def _load_gmf_set_ids(self):
        """
        At the moment, we only support risk calculations using ground motion
        fields coming from a specific realization.
        """
        gmf_collection = models.GmfCollection.objects.get(
            id=self._hazard_output_id)

        if gmf_collection.output.output_type == "gmf":
            return tuple(
                gmf_collection.gmfset_set.values_list('id', flat=True))
        else:
            raise ValueError(
                "Output must be of type `gmf`. "
                "At the moment, we only support computation of loss curves "
                "for a specific logic tree branch.")

    # Note on the algorithm: the idea is to first compute the minimal distance
    # between the given site and the ground motion fields in the mesh; then the
    # ground motion values are extracted from the points at that distance. To
    # cope with numerical errors we extract all the ground motion fields within
    # the minimal distance plus 10 centimers (any "small" number would do).
    # This is ~6 times faster than using a group by/order by to extract the
    # locations/gmvs directly with a single query.
    def __call__(self, site):
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
        args = ("SRID=4326; %s" % site.wkt, self._imt, self._gmf_set_ids)

        if self._imt == "SA":
            spectral_filters = "AND sa_period = %s AND sa_damping = %s"
            args += (self._sa_period, self._sa_damping)

        min_dist_query = """-- find the distance of the closest location
        SELECT min(ST_Distance_Sphere(location, %s)) FROM hzrdr.gmf
        WHERE imt = %s AND gmf_set_id IN %s {}""".format(
            spectral_filters)

        min_dist = _get_min_distance(self, cursor, min_dist_query, args)

        gmvs_query = """-- return all the gmvs inside the min_dist radius
        SELECT gmvs FROM hzrdr.gmf
        WHERE %s > ST_Distance_Sphere(location, %s)
        AND imt = %s AND gmf_set_id IN %s {}
        ORDER BY gmf_set_id, result_grp_ordinal
        """.format(spectral_filters)

        cursor.execute(gmvs_query, (min_dist,) + args)

        ground_motion_values = sum([row[0] for row in cursor], [])
        self._cache[site.wkt] = ground_motion_values
        return ground_motion_values


class GroundMotionScenarioGetter(object):
    """
    Hazard getter for loading ground motion values from the table
    gmf_scenario.
    It caches the ground motion values on a per-location basis.

    :param int hazard_output_id:
        Id of the hazard output (`openquake.db.models.Output`) used to
        look up the ground motion values. This implementation only supports
        plain `gmf` output types (single logic tree branch or realization).
    :param str imt:
        The intensity measure type with which the ground motion
        values have been computed (long form).
    """

    def __init__(self, hazard_output_id, imt):
        imt, sa_period, sa_damping = models.parse_imt(imt)

        self._imt = imt
        self._sa_period = sa_period
        self._sa_damping = sa_damping
        self._hazard_output_id = hazard_output_id
        self._cache = {}

    # this is basically the same algorithm used in GroundMotionValuesGetter
    def __call__(self, site):
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
        args = ("SRID=4326; %s" % site.wkt, self._imt, self._hazard_output_id)

        if self._imt == "SA":
            spectral_filters = "AND sa_period = %s AND sa_damping = %s"
            args += (self._sa_period, self._sa_damping)

        min_dist_query = """-- find the distance of the closest location
        SELECT min(ST_Distance_Sphere(location, %s)) FROM hzrdr.gmf_scenario
        WHERE imt = %s AND output_id = %s {}""".format(
            spectral_filters)

        min_dist = _get_min_distance(self, cursor, min_dist_query, args)

        gmvs_query = """-- return all the gmvs inside the min_dist radius
        SELECT gmvs FROM hzrdr.gmf_scenario
        WHERE %s > ST_Distance_Sphere(location, %s)
        AND imt = %s AND output_id = %s {}
        ORDER BY result_grp_ordinal
        """.format(spectral_filters)

        cursor.execute(gmvs_query, (min_dist,) + args)

        ground_motion_values = sum([row[0] for row in cursor], [])
        self._cache[site.wkt] = ground_motion_values
        return ground_motion_values
