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

"""Hazard getters for Risk calculators."""

from openquake.db import models


# TODO: Optimize this, as it is very slow
class HazardCurveGetterPerAsset(object):
    def __init__(self, hazard_curve_id):
        self.hazard_curve_id = hazard_curve_id
        self.imls = models.HazardCurve.objects.get(pk=hazard_curve_id).imls

    def __call__(self, site):
        """
        :param location:
            `django.contrib.gis.geos.point.Point` object
        :param int hazard_curve_id:
            ID of a `hzrdr.hazard_curve` record, telling us which set of hazard
            curves to query for the closest curve.
        """
        query = """
        SELECT
            hzrdr.hazard_curve_data.*,
            min(ST_Distance_Sphere(location, %s))
                AS min_distance
        FROM hzrdr.hazard_curve_data
        WHERE hazard_curve_id = %s
        GROUP BY id
        ORDER BY min_distance
        LIMIT 1;"""

        args = ('SRID=4326; %s' % site.wkt, self.hazard_curve_id)
        raw_query_set = models.HazardCurveData.objects.raw(query, args)

        [haz_curve_data] = list(raw_query_set)

        return zip(self.imls, haz_curve_data['poes'])


HAZARD_GETTERS = dict(
    one_query_per_asset=HazardCurveGetterPerAsset
    )
