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

    def __init__(self, owner=None):
        """Create a new serializer for the specified user"""
        self.model = None
        if owner:
            self.owner = owner
        else:
            self.owner = models.OqUser.objects.get(user_name="openquake")

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
                owner=self.owner,
                description=values.get("listDescription"),
                category=values["assetCategory"],
                area_type=values["areaType"], area_unit=values["areaUnit"],
                coco_type=values["cocoType"], coco_unit=values["cocoUnit"],
                reco_type=values["recoType"], reco_unit=values["recoUnit"],
                stco_type=values["stcoType"], stco_unit=values["stcoUnit"])
            self.model.save()

        data = models.ExposureData(
            exposure_model=self.model, asset_ref=values["assetID"],
            coco=values["coco"], reco=values["reco"],
            stco=values["stco"], area=values["area"],
            number_of_units=values["number"],
            coco_deductible=values["deductible"],
            coco_limit=values["limit"], taxonomy=values["taxonomy"],
            site="POINT(%s %s)" % (point.point.x, point.point.y))
        data.save()
