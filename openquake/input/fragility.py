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


"""Saves fragility model data to the database"""

import itertools

from openquake.db import models
from django.db import router
from django.db import transaction


class FragilityDBWriter(object):
    """
    Serialize the fragility model to database
    """

    lsi = None
    model_attrs = [
        ("description", "description"), ("imls", "imls"), ("imt", "imt")]

    def __init__(self, smi, parser, owner=None):
        """Create a new serializer for the specified user

        :param smi: source model input
        :type smi: :class:`openquake.db.models.Input`
        :param parser: fragility model data
        :type parser: :class:`openquake.parser.fragility.FragilityModelParser`
        :param owner: the user that should own the model
        :type owner: :class:`openquake.db.models.OqUser`
        """
        self.smi = smi
        if owner:
            self.owner = owner
        else:
            self.owner = smi.owner
        self.parser = parser
        self.model = None

    @transaction.commit_on_success(router.db_for_write(models.FragilityModel))
    def serialize(self):
        """
        Serialize a list of values produced by
        :class:`openquake.parser.fragility.FragilityModelParser`
        """
        for ff in self.parser:
            self.insert_datum(ff)

    def insert_datum(self, ff):
        """
        Insert a single fragility function (either discrete or continuous).

        :param ff: fragility function
        :type ff: one of :class:`openquake.parser.fragility.FFC` or
            :class:`openquake.parser.fragility.FFD`

        It also inserts the fragility model entry if not already present.
        """
        if not self.model:
            fragm = self.parser.model
            self.model = models.FragilityModel(
                owner=self.owner, input=self.smi, lss=fragm.limits,
                format=fragm.format)
            for key, tag in self.model_attrs:
                value = getattr(fragm, tag)
                if value:
                    if tag == "imt":
                        value = value.lower()
                    setattr(self.model, key, value)
            self.model.save()
            self.lsi = dict(zip(self.model.lss, itertools.count(1)))

        discrete = self.model.format == "discrete"
        ctor = models.Ffd if discrete else models.Ffc
        data = ctor(
            fragility_model=self.model, taxonomy=ff.taxonomy, ls=ff.limit,
            lsi=self.lsi[ff.limit])
        if discrete:
            data.poes = ff.poes
        else:
            if ff.type:
                data.ftype = ff.type
            data.mean = ff.mean
            data.stddev = ff.stddev
        data.save()
