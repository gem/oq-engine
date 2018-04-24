# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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
from openquake.baselib import sap, datastore, general


def make_figure(losses_by_event, loss_types):
    """
    :param losses_by_event: composite array (eid, rlzi, losses)
    :param loss_types: list of loss types
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt
    losses_by_rlzi = general.group_array(losses_by_event, 'rlzi')
    R = len(losses_by_rlzi)
    L = losses_by_rlzi[0]['loss'].shape[1]
    fig = plt.figure()
    for rlzi in losses_by_rlzi:
        loss_array = losses_by_rlzi[rlzi]['loss']
        print('rlzi=%d, num_events=%d' % (rlzi, len(loss_array)))
        for lti, lt in enumerate(loss_types):
            losses = loss_array[:, lti]
            ax = fig.add_subplot(R, L, rlzi * L + lti + 1)
            ax.set_xlabel('rlz=%d, loss_type=%s' % (rlzi, lt))
            ax.hist(losses, 7, rwidth=.9)
            ax.set_title('loss=%.5e$\pm$%.5e' %
                         (losses.mean(), losses.std(ddof=1)))
    return plt


@sap.Script
def plot_losses(calc_id):
    """
    losses_by_event plotter
    """
    # read the hazard data
    dstore = datastore.read(calc_id)
    oq = dstore['oqparam']
    plt = make_figure(dstore['agg_loss_table'].value, oq.loss_dt().names)
    plt.show()

plot_losses.arg('calc_id', 'a computation id', type=int)
