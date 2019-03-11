# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
import sys
from openquake.baselib import sap
from openquake.commonlib import util


def make_figure(periods, losses):
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt
    loss_types = losses.dtype.names
    num_lt = len(loss_types)
    fig = plt.figure()
    for j, lt in enumerate(loss_types, 1):
        ax = fig.add_subplot(num_lt, 1, j)
        ax.grid(True)
        ax.set_ylabel(lt)
        for s, losses_ in enumerate(losses[lt].T):
            ax.plot(periods, losses_, label=str(s))
    if losses.shape[1] < 20:  # show legend only if < 20 realizations
        plt.legend(loc='lower right')
    return plt


@sap.script
def plot_lc(calc_id, aid=None):
    """
    Plot loss curves given a calculation id and an asset ordinal.
    """
    # read the hazard data
    dstore = util.read(calc_id)
    dset = dstore['agg_curves-rlzs']
    if aid is None:  # plot the global curves
        plt = make_figure(dset.attrs['return_periods'], dset.value)
    else:
        sys.exit('Not implemented yet')
    plt.show()


plot_lc.arg('calc_id', 'a computation id', type=int)
plot_lc.arg('aid', 'asset ordinal', type=int)
