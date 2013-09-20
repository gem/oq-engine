# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
Serializer and related functions to save exposure data to the database.
"""

from openquake.engine.db import models
from django.db import router
from django.db import transaction


class ExposureDBWriter(object):
    """
    Serialize the exposure model to database

    :attr exposure_input:
        an instance of :class:`openquake.engine.db.models.Input` representing
        an exposure input
    """

    def __init__(self, exposure_input):
        """Create a new serializer"""
        self.exposure_input = exposure_input
        self.model = None
        self.conversions = {}

    @transaction.commit_on_success(router.db_for_write(models.ExposureModel))
    def serialize(self, iterator):
        """
        Serialize a list of values produced by iterating over an instance of
        :class:`openquake.nrmllib.risk.parsers.ExposureParser`
        """
        for point, occupancy, values, costs, conversions in iterator:
            self.insert_datum(point, occupancy, values, costs, conversions)

    def insert_datum(self, point, occupancy, values, costs, conversions):
        """
        Insert a single asset entry.

        :param list point:
            Asset location (format [lon, lat]).
        :param list occupancy:
            A potentially empty list of named tuples
            each one having an 'occupants' and a 'period' property.
        :param dict values:
            Asset attributes (see
            :class:`openquake.nrmllib.risk.parsers.ExposureModelParser`).
        :param list costs:
            A potentially empty list of named tuples
            each one having the following fields:
            type, value, retrofitted, deductible and limit.
        :param dict conversions:
            A potentially empty dict with conversion, mapping cost types to
            conversion types (per_area, aggregated, per_unit)

        It also inserts the main exposure model entry if
        not already present.
        """

        if not self.model:
            self.model = models.ExposureModel.objects.create(
                input=self.exposure_input,
                name=values["exposureID"],
                description=values.get("description"),
                taxonomy_source=values.get("taxonomySource"),
                category=values["category"],
                area_type=values.get("areaType"),
                area_unit=values.get("areaUnit"),
                deductible_absolute=values.get("deductibleIsAbsolute"),
                insurance_limit_absolute=values.get("limitIsAbsolute"))

            for name, (conversion, unit,
                       retrofitted_conversion, retrofitted_unit) in (
                           conversions.items()):
                self.conversions[name] = models.CostType.objects.create(
                    exposure_model=self.model,
                    name=name,
                    conversion=conversion,
                    unit=unit,
                    retrofitted_conversion=retrofitted_conversion,
                    retrofitted_unit=retrofitted_unit)

        asset = models.ExposureData.objects.create(
            exposure_model=self.model, asset_ref=values["id"],
            taxonomy=values.get("taxonomy"),
            area=values.get("area"),
            number_of_units=values.get("number"),
            site="POINT(%s %s)" % (point[0], point[1]))

        for cost_type in self.conversions:
            if not any([cost_type == cost.type for cost in costs]):
                raise ValueError("Invalid Exposure. "
                                 "Missing cost %s for asset %s" % (
                                     cost_type, asset.asset_ref))

        for cost in costs:
            cost_type = self.conversions.get(cost.type, None)

            if cost_type is None:
                raise ValueError("Invalid Exposure. Missing conversion "
                                 "for cost type %s" % cost.type)

            if cost.retrofitted is not None:
                retrofitted = models.ExposureData.per_asset_value(
                    cost.retrofitted, cost_type.retrofitted_conversion,
                    asset.area, values.get("areaType"),
                    asset.number_of_units, values["category"])
            else:
                retrofitted = None

            converted_cost = models.ExposureData.per_asset_value(
                cost.value, cost_type.conversion,
                asset.area, values.get("areaType"),
                asset.number_of_units, values["category"])
            models.Cost.objects.create(
                exposure_data=asset,
                cost_type=cost_type,
                converted_cost=converted_cost,
                converted_retrofitted_cost=retrofitted,
                deductible_absolute=models.make_absolute(
                    cost.deductible,
                    converted_cost,
                    values.get("deductibleIsAbsolute", True)),
                insurance_limit_absolute=models.make_absolute(
                    cost.limit,
                    converted_cost,
                    values.get("insuranceLimitIsAbsolute", True)))

        for odata in occupancy:
            models.Occupancy.objects.create(exposure_data=asset,
                                            occupants=odata.occupants,
                                            period=odata.period)
