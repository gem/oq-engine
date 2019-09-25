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
import numpy
from openquake.baselib import sap
from openquake.calculators.extract import extract
from openquake.commonlib import util


def make_figure(losses_by_rlzi, loss_types, nbins):
    """
    :param losses_by_event: composite array (eid, rlzi, losses)
    :param loss_types: list of loss types
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt
    R = len(losses_by_rlzi)
    L = len(loss_types)
    fig = plt.figure()
    for rlz in losses_by_rlzi:
        rlzi = int(rlz[4:])  # strip rlz-
        losses = losses_by_rlzi[rlz]['loss'].reshape(-1, L)
        print('%s, num_events=%d' % (rlz, len(losses)))
        for lti, lt in enumerate(loss_types):
            ls = losses[:, lti]
            if numpy.isnan(ls).all():
                continue
            ax = fig.add_subplot(R, L, rlzi * L + lti + 1)
            ax.set_xlabel('%s, loss_type=%s' % (rlz, lt))
            ax.hist(ls, nbins, rwidth=.9)
            ax.set_title('loss=%.5e$\pm$%.5e' % (ls.mean(), ls.std(ddof=1)))
    return plt


@sap.script
def plot_losses(calc_id, bins=7):
    """
    losses_by_event plotter
    """
    # read the hazard data
    dstore = util.read(calc_id)
    losses_by_rlzi = dict(extract(dstore, 'losses_by_event'))
    oq = dstore['oqparam']
    plt = make_figure(losses_by_rlzi, oq.loss_dt().names, bins)
    plt.show()


plot_losses.arg('calc_id', 'a computation id', type=int)
plot_losses.opt('bins', 'number of histogram bins', type=int)
