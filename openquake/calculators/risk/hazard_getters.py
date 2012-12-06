# -*- coding: utf-8 -*-

# Copyright (c) 2010-2012, GEM Foundation.
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
            `django.contrib.gis.geos.point.Point` object
        :param int hazard_curve_id:
            ID of a `hzrdr.hazard_curve` record, telling us which set of hazard
            curves to query for the closest curve.
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


class GroundMotionValuesGetter(object):
    """
    Hazard getter for loading ground motion values.
    It caches the ground motion values on a per-location basis.

    :param integer hazard_output_id:
        The id of hazard output (`openquake.db.models.Output`) used to
        look up the ground motion values. This implementation only supports
        plain `gmf` output types.
    :param str imt:
        The intensity measure type with which the ground motion
        values have been computed.
    :param float time_span:
        Time span (also known as investigation time).
    :param float tses:
        Time representative of the stochastic event set.
        It is computed as: time span * number of logic tree branches *
        number of seismicity histories.
    """

    def __init__(self, hazard_output_id, imt, time_span, tses):
        self._imt = imt
        self._tses = tses
        self._time_span = time_span

        self._cache = {}

        self._gmf_set_ids = tuple(
            [x.id for x in models.GmfSet.objects.filter(
            gmf_collection__output=hazard_output_id)])

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

        query = """
        SELECT array_agg(n.v) as t, min(ST_Distance_Sphere(location, %s))
        AS min_distance FROM (
            SELECT unnest(gmvs) as v, location FROM hzrdr.gmf
            WHERE imt = %s AND gmf_set_id IN %s
            ORDER BY result_grp_ordinal
        ) n GROUP BY location ORDER BY min_distance LIMIT 1;"""

        args = ("SRID=4326; %s" % site.wkt, self._imt, self._gmf_set_ids)

        cursor.execute(query, args)
        ground_motion_values = cursor.fetchone()[0]

        # temporary format, to be changed.
        result = {"IMLs": ground_motion_values,
            "TimeSpan": self._time_span, "TSES": self._tses}

        self._cache[site.wkt] = result
        return result


HAZARD_GETTERS = dict(
    one_query_per_asset=HazardCurveGetterPerAsset,
    event_based=GroundMotionValuesGetter,
)
