# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
Serializer and related functions to save exposure data to the database.
"""

import os

from openquake.db import models
from django.db import router
from django.db import transaction

from openquake.parser import exposure
from openquake import shapes


class ExposureDBWriter(object):
    """
    Serialize the exposure model to database
    """

    model_attrs = [
        ("area_type", "areaType"), ("area_unit", "areaUnit"),
        ("coco_type", "cocoType"), ("coco_unit", "cocoUnit"),
        ("reco_type", "recoType"), ("reco_unit", "recoUnit"),
        ("stco_type", "stcoType"), ("stco_unit", "stcoUnit")]

    def __init__(self, smi, owner=None):
        """Create a new serializer for the specified user"""
        self.smi = smi
        if owner:
            self.owner = owner
        else:
            self.owner = smi.owner
        self.model = None

    @transaction.commit_on_success(router.db_for_write(models.ExposureModel))
    def serialize(self, iterator):
        """
        Serialize a list of values produced by
        :class:`openquake.parser.exposure.ExposureModelFile`

        :type iterator: any iterable
        """
        for point, occupancy, values in iterator:
            self.insert_datum(point, occupancy, values)

    def insert_datum(self, point, occupancy, values):
        """
        Insert a single asset entry.

        :param point: asset location
        :type point: :class:`openquake.shapes.Site`
        :param list occupancy: a potentially empty list of named tuples
            each having an 'occupants' and a 'description' property
        :param values: dictionary of values (see
            :class:`openquake.parser.exposure.ExposureModelFile`)

        it also inserts the main exposure model entry if not already
        present,
        """
        if not self.model:
            self.model = models.ExposureModel(
                owner=self.owner, input=self.smi,
                description=values.get("listDescription"),
                taxonomy_source=values.get("taxonomySource"),
                category=values["assetCategory"])
            for key, tag in self.model_attrs:
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
            ("deductible", "deductible"), ("ins_limit", "limit")]:
            value = values.get(tag)
            if value:
                setattr(data, key, value)
        data.save()
        for odata in occupancy:
            oobj = models.Occupancy(exposure_data=data,
                                    occupants=odata.occupants,
                                    description=odata.description)
            oobj.save()


def read_sites_from_exposure(job_ctxt):
    """
    Given a :class:`JobContext` object, get all of the sites in the exposure
    model which are contained by the region of interest (defined in the
    `JobContext`).

    It is assumed that exposure model is already loaded into the database.

    :param job_ctxt:
        :class:`JobContext` instance.
    :returns:
        `list` of :class:`openquake.shapes.Site` objects, with no duplicates
    """

    em_inputs = models.inputs4job(job_ctxt.job_id, input_type="exposure")
    exp_points = models.ExposureData.objects.filter(
        exposure_model__input__id__in=[em.id for em in em_inputs],
        site__contained=job_ctxt.oq_job_profile.region).values(
        'site').distinct()

    return [shapes.Site(p['site'].x, p['site'].y) for p in exp_points]


def store_exposure_assets(job_id, base_path):
    """
    Load exposure assets from input file and store them
    into database.

    If the given job already has an input of type `exposure`,
    this function simply returns without doing anything.

    :param job_id: the id of the job where the assets
        belong to.
    :type job_id: integer
    :param base_path: the path where the application has been
        triggered. It is used to properly locate the input
        files, that are stored with a relative path.
    :type base_path: string
    """

    [emi] = models.inputs4job(job_id, "exposure")
    if emi.exposuremodel_set.all().count() > 0:
        return

    path = os.path.join(base_path, emi.path)
    exposure_parser = exposure.ExposureModelFile(path)
    writer = ExposureDBWriter(emi)
    writer.serialize(exposure_parser)
