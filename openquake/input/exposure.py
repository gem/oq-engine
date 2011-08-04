# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
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

from db.alchemy import models


class ExposureDBWriter(object):
    """
    Serialize the exposure model to database
    """

    def __init__(self, session):
        """Create a new serializer using the specific session"""
        self.session = session
        self.model = None

    def serialize(self, iterator):
        """
        Serialize a list of values produced by
        :class:`openquake.parser.exposure.ExposurePortfolioFile`

        :type iterator: any iterable
        """
        for point, values in iterator:
            self.insert_datum(point, values)

        self.session.commit()

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
                description=values.get('listDescription'),
                category=values['assetCategory'],
                unit=values['assetValueUnit'])
            self.session.add(self.model)

        data = models.ExposureModelData(
            exposure_model=self.model, asset_ref=values['assetID'],
            value=values['assetValue'],
            vf_ref=values['vulnerabilityFunctionReference'],
            structure_type=values['structureCategory'],
            site="POINT(%s %s)" % (point.point.x, point.point.y),
            retrofitting_cost=None)
        self.session.add(data)
