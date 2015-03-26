#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import cPickle
from openquake.commonlib import sap, valid
from openquake.baselib.general import ArrayDict
from openquake.commonlib.commands.plot import combined_curves
from openquake.commonlib.util import rmsep


def pick_rlzs(hazard_pik, min_value=0.01):
    """
    An utility to print out the realizations, in order of distance
    from the mean.

    :param hazard_pik:
        the pathname to a pickled file containing the hazard curves
    """
    # read the hazard data
    with open(hazard_pik) as f:
        haz = cPickle.load(f)
    curves_by_rlz, mean_curves = combined_curves(haz, hazard_pik)
    dists = []
    for rlz in sorted(curves_by_rlz):
        mean = ArrayDict(mean_curves)
        arr = ArrayDict(curves_by_rlz[rlz])
        dists.append((rmsep(mean, arr, min_value), rlz))
    for dist, rlz in sorted(dists):
        print 'rlz=%s, rmsep=%s' % (rlz, dist)

parser = sap.Parser(pick_rlzs)
parser.arg('hazard_pik', '.pik file containing the result of a computation')
parser.arg('min_value', 'ignore poes lower than that',
           type=valid.positivefloat)
