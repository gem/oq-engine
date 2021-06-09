# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021, GEM Foundation
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

from openquake.hazardlib.geo.packager import fiona
from openquake.hazardlib.nrml_to import convert_to as main

main.fmt = dict(help='csv or gpkg',
                choices=['csv', 'gpkg'] if fiona else ['csv'])
main.fnames = dict(help='source model files in XML', nargs='+')
main.chatty = 'display sources in progress'
main.outdir = 'output directory'
main.geometry = 'geometry model file'
