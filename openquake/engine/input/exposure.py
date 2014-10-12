# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2014, GEM Foundation.
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

    :attr job:
        an instance of :class:`openquake.engine.db.models.OqJob`
    """

    def __init__(self, job):
        """Create a new serializer"""
        self.job = job
        self.model = None
        self.cost_types = {}

    @transaction.commit_on_success(router.db_for_write(models.ExposureModel))
    def serialize(self, iterator):
        """
        Serialize a list of values produced by iterating over an instance of
        :class:`openquake.commonlib.risk_parsers.ExposureParser`
        """
        for asset_data in iterator:
            if not self.model:
                self.model, self.cost_types = (
                    self.insert_model(asset_data.exposure_metadata))
            self.insert_datum(asset_data)
        return self.model

    def insert_model(self, model):
        """
        :returns:
            a 2-tuple holding a newly created instance of
            :class:`openquake.engine.db.models.ExposureModel` and
            a dictionary of (newly created)
            :class:`openquake.engine.db.models.ExposureModel` instances
            keyed by the cost type name

        :param model:
            an instance of
            :class:`openquake.commonlib.risk_parsers.ExposureMetadata`
        """
        exposure_model = models.ExposureModel.objects.create(
            job=self.job,
            name=model.exposure_id,
            description=model.description,
            taxonomy_source=model.taxonomy_source,
            category=model.asset_category,
            area_type=model.conversions.area_type,
            area_unit=model.conversions.area_unit,
            deductible_absolute=model.conversions.deductible_is_absolute,
            insurance_limit_absolute=(
                model.conversions.insurance_limit_is_absolute))

        cost_types = {}
        for cost_type in model.conversions.cost_types:
            cost_types[cost_type.name] = models.CostType.objects.create(
                exposure_model=exposure_model,
                name=cost_type.name,
                conversion=cost_type.conversion_type,
                unit=cost_type.unit,
                retrofitted_conversion=cost_type.retrofitted_type,
                retrofitted_unit=cost_type.retrofitted_unit)

        return exposure_model, cost_types

    def insert_datum(self, asset_data):
        """
        Insert a single asset entry.

        :param asset_data:
            an instance of :class:`openquake.commonlib.risk_parsers.AssetData`
        """
        asset = models.ExposureData.objects.create(
            exposure_model=self.model,
            asset_ref=asset_data.asset_ref,
            taxonomy=asset_data.taxonomy,
            area=asset_data.area,
            number_of_units=asset_data.number,
            site="POINT(%s %s)" % (asset_data.site.longitude,
                                   asset_data.site.latitude))

        for cost_type in self.cost_types:
            if not any([cost_type == cost.cost_type
                        for cost in asset_data.costs]):
                raise ValueError("Invalid Exposure. "
                                 "Missing cost %s for asset %s" % (
                                     cost_type, asset.asset_ref))

        model = asset_data.exposure_metadata
        deductible_is_absolute = model.conversions.deductible_is_absolute
        insurance_limit_is_absolute = (
            model.conversions.insurance_limit_is_absolute)

        for cost in asset_data.costs:
            cost_type = self.cost_types.get(cost.cost_type, None)

            if cost_type is None:
                raise ValueError("Invalid Exposure. Missing conversion "
                                 "for cost type %s" % cost.cost_type)

            if cost.retrofitted is not None:
                retrofitted = models.ExposureData.per_asset_value(
                    cost.retrofitted, cost_type.retrofitted_conversion,
                    asset_data.area,
                    model.conversions.area_type,
                    asset_data.number,
                    model.asset_category)
            else:
                retrofitted = None

            converted_cost = models.ExposureData.per_asset_value(
                cost.value, cost_type.conversion,
                asset_data.area,
                model.conversions.area_type,
                asset_data.number,
                model.asset_category)

            models.Cost.objects.create(
                exposure_data=asset,
                cost_type=cost_type,
                converted_cost=converted_cost,
                converted_retrofitted_cost=retrofitted,
                deductible_absolute=models.make_absolute(
                    cost.deductible,
                    converted_cost,
                    deductible_is_absolute),
                insurance_limit_absolute=models.make_absolute(
                    cost.limit,
                    converted_cost,
                    insurance_limit_is_absolute))

        for odata in asset_data.occupancy:
            models.Occupancy.objects.create(exposure_data=asset,
                                            occupants=odata.occupants,
                                            period=odata.period)
