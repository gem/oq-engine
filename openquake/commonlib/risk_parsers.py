# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2016 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module containing parsers for risk input artifacts.
"""
from openquake.commonlib.node import iterparse
from collections import namedtuple

from openquake.commonlib import nrml

NRML = "{%s}" % nrml.NAMESPACE
GML = "{%s}" % nrml.GML_NAMESPACE

AssetData = namedtuple(
    "AssetData",
    "exposure_metadata site asset_ref taxonomy area number costs occupancy")
Site = namedtuple("Site", "longitude latitude")
ExposureMetadata = namedtuple(
    "ExposureMetadata",
    "exposure_id taxonomy_source asset_category description conversions")


class Conversions(object):
    def __init__(self, cost_types, area_type, area_unit,
                 deductible_is_absolute, insurance_limit_is_absolute):
        self.cost_types = cost_types
        self.area_type = area_type
        self.area_unit = area_unit
        self.deductible_is_absolute = deductible_is_absolute
        self.insurance_limit_is_absolute = insurance_limit_is_absolute

    def __repr__(self):
        return str(self.__dict__)

    def __eq__(self, cs):
        return (
            self.cost_types == cs.cost_types and
            self.area_type == cs.area_type and
            self.area_unit == cs.area_unit and
            self.deductible_is_absolute == cs.deductible_is_absolute and
            self.insurance_limit_is_absolute == cs.insurance_limit_is_absolute)
