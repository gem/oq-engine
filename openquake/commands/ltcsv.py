# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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

import logging
from openquake.baselib.writers import write_csv
from openquake.hazardlib.logictree import SourceModelLogicTree


def main(fname, out=None):
    """
    Convert logic tree source model file from XML into CSV
    """
    smlt = SourceModelLogicTree(fname)
    array, attrs = smlt.__toh5__()
    if out is None:
        out = fname[:-4] + '.csv'
    write_csv(out, array, comment=attrs)
    logging.info('Saved %s', out)


main.fname = 'path to the XML source model logic tree'
main.out = 'path to the CSV source model logic tree'
