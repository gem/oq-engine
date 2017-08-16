# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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

from __future__ import print_function
import numpy
from openquake.baselib import sap
from openquake.commonlib import datastore


def make_figure(asset, loss_ratios, rcurves):
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt
    loss_types = rcurves.dtype.names
    S, I = rcurves.shape
    num_lt = len(loss_types)
    fig = plt.figure()
    for j, lt in enumerate(loss_types, 1):
        losses = asset.value(lt) * numpy.array(loss_ratios[lt])
        for i in range(I):
            ax = fig.add_subplot(num_lt * I, I, i * num_lt + j)
            ax.grid(True)
            ax.set_ylabel('%s%s' % (lt, '_ins' if i else ''))
            ax.set_ylim([0, 1])
            for s, poes in enumerate(rcurves[lt][i]):
                ax.plot(losses, poes, label=str(s))
    plt.legend()
    return plt


@sap.Script
def plot_lc(calc_id, aid):
    """
    Plot loss curves given a calculation id and an asset ordinal.
    """
    # read the hazard data
    dstore = datastore.read(calc_id)
    oq = dstore['oqparam']
    asset = dstore['assetcol'][aid]
    plt = make_figure(asset, oq.loss_ratios, dstore['rcurves-stats'][aid])
    plt.show()

plot_lc.arg('calc_id', 'a computation id', type=int)
plot_lc.arg('aid', 'asset ordinal', type=int)
