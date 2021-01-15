# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import os.path
from openquake.commonlib import shapefileparser


def main(input_shp_files, validate=False, *, output=None):
    """
    Convert multiple ESRI Shapefile(s) into a single NRML source model file.
    """
    input_parser = shapefileparser.ShapefileParser()
    source_model = input_parser.read(input_shp_files[0], validate)
    for f in input_shp_files[1:]:
        source_model.sources.extend(input_parser.read(f, validate).sources)
    if not output:
        output = os.path.splitext(input_shp_files[0])[0]
    shapefileparser.SourceModelParser().write(output + '.xml', source_model)


main.input_shp_files = dict(
    help='path(s) to source model ESRI shapefile(s)', nargs='+')
main.validate = 'Apply validation to input model (can be slow)'
main.output = 'output path (no extension)'
