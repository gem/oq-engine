# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
from openquake.baselib import sap
from openquake.commonlib import shapefileparser


@sap.script
def to_shapefile(output, input_nrml_file, validate):
    """
    Convert a NRML source model file to ESRI Shapefile(s).

    For each type of source geometry defined in the NRML file (point, area,
    simple fault, complex fault, planar) a separate shapefile is created. Each
    shapefile is differentiated by a specific ending('_point', '_area',
    '_simple', '_complex', '_planar').

    NB: nonparametric sources are not supported.
    """
    input_parser = shapefileparser.SourceModelParser()
    source_model = input_parser.read(input_nrml_file, validate)
    if not output:
        output = os.path.splitext(input_nrml_file)[0]
    print('Extracting %s_ files' % output)
    shapefileparser.ShapefileParser().write(output, source_model)

to_shapefile.opt('output', 'output path (no extension)')
to_shapefile.arg('input_nrml_file', 'path to source model NRML file')
to_shapefile.flg('validate', 'Apply validation to input model (can be slow)')
