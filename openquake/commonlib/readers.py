#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2016, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import operator
import numpy
from openquake.baselib.general import groupby, DictArray

F32 = numpy.float32


class CurveReader(object):
    """
    A reader for hazard curves stored in a CSV file. The usage is as follows:

    >> cr = CurveReader('/path/to/hcurves.csv')
    >> for curve in cr.read():
    ..     for imt in cr.imtls:
    ..         print imt, cr.imtls[imt], curve
    """
    def __init__(self, fname):
        self.fname = fname
        with open(fname) as f:
            header = next(f).split(',')
        self.imtls, self.fields = self._parse_header(header)

    def _parse_header(self, header):
        fields = []  # pairs (name, dtype), for instance ('PGA', F32)
        cols = []  # pairs (name, float), for instance ('PGA', 0.1)
        for col in header:
            if '-' in col:  # for instance PGA-0.1
                cols.append(col.split('-', 1))
            else:  # for lon and lat
                fields.append((col, F32))
        imtls = {}
        for imt, imls in groupby(
                cols, operator.itemgetter(0),
                lambda g: [F32(r[1]) for r in g]).items():
            fields.append((imt, (F32, len(imls))))
            imtls[imt] = imls
        return DictArray(imtls), fields

    def read(self):
        """
        :returns: composite array (lon, lat, IMT1, ...  IMTN)
        """
        array = numpy.loadtxt(self.fname, dtype=F32, delimiter=',', skiprows=1)
        return array.view(numpy.dtype(self.fields))
