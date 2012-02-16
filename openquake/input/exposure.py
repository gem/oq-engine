# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""Serializer to save exposure data to the database"""

from openquake.db import models
from django.db import router
from django.db import transaction


class ExposureDBWriter(object):
    """
    Serialize the exposure model to database
    """

    def __init__(self, input_set, path, owner=None):
        """Create a new serializer for the specified user"""
        qargs = dict(input_type="exposure", path=path)
        [self.input] = input_set.input_set.filter(**qargs)
        if owner:
            self.owner = owner
        else:
            self.owner = models.OqUser.objects.get(user_name="openquake")
        self.model = None

    @transaction.commit_on_success(router.db_for_write(models.ExposureModel))
    def serialize(self, iterator):
        """
        Serialize a list of values produced by
        :class:`openquake.parser.exposure.ExposurePortfolioFile`

        :type iterator: any iterable
        """
        for point, values in iterator:
            self.insert_datum(point, values)

    def insert_datum(self, point, values):
        """
        Insert a single asset entry.

        :param point: asset location
        :type point: :class:`openquake.shapes.Site`

        :param values: dictionary of values (see
            :class:`openquake.parser.exposure.ExposurePortfolioFile`)

        it also inserts the main exposure model entry if not already
        present,
        """
        if not self.model:
            self.model = models.ExposureModel(
                owner=self.owner, input=self.input,
                description=values.get("listDescription"),
                category=values["assetCategory"])
            for key, tag in [
                ("area_type", "areaType"), ("area_unit", "areaUnit"),
                ("coco_type", "cocoType"), ("coco_unit", "cocoUnit"),
                ("reco_type", "recoType"), ("reco_unit", "recoUnit"),
                ("stco_type", "stcoType"), ("stco_unit", "stcoUnit")]:
                value = values.get(tag)
                if value:
                    setattr(self.model, key, value)
            self.model.save()

        data = models.ExposureData(
            exposure_model=self.model, asset_ref=values["assetID"],
            taxonomy=values.get("taxonomy"),
            site="POINT(%s %s)" % (point.point.x, point.point.y))
        for key, tag in [
            ("coco", "coco"), ("reco", "reco"), ("stco", "stco"),
            ("area", "area"), ("number_of_units", "number"),
            ("coco_deductible", "deductible"), ("coco_limit", "limit")]:
            value = values.get(tag)
            if value:
                setattr(data, key, value)
        data.save()
