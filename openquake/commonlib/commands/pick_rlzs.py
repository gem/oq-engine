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
import operator
import collections
from openquake.commonlib import sap
from openquake.baselib.general import groupby
from openquake.commonlib.commands.plot import combined_curves
from openquake.commonlib.util import max_rel_diff_index

MaxDiff = collections.namedtuple('MaxDiff', 'maxdiff rlz imt site_idx')


def max_diff(rows):
    return max(row.maxdiff for row in rows)


def pick_rlzs(hazard_pik):
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
    diffs = []
    for rlz in sorted(curves_by_rlz):
        for imt in mean_curves:
            maxdiff, site = max_rel_diff_index(
                mean_curves[imt], curves_by_rlz[rlz][imt])
            diffs.append(MaxDiff(maxdiff, rlz, imt, site))
    groups = groupby(diffs, operator.attrgetter('rlz')).values()
    for group in sorted(groups, key=max_diff):
        for md in sorted(group):
            print 'rlz=%s, IMT=%s, max_diff=%s at site %d' % (
                md.rlz, md.imt, md.maxdiff, md.site_idx)
        print

parser = sap.Parser(pick_rlzs)
parser.arg('hazard_pik', '.pik file containing the result of a computation')
