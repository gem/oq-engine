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
from openquake.commonlib import sap


def make_figure(output_key, losses, poes):
    """
    Plot a loss curve
    """
    # NB: matplotlib is imported inside, otherwise nosetest would fail in an
    # installation without matplotlib
    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.grid(True)
    ax.set_ylim([0, 1])
    ax.set_xlabel(output_key)
    ax.set_ylabel('PoE')
    ax.plot(losses, poes)
    return plt


def plot_loss(risk_pik, output_key):
    """
    Loss curves plotter. For the moment it is restricted to the
    aggregate curves.

    :param risk_pik: the pathname to a pickled file
    :param output_key: an unique string for the output to plot
    """
    # read the data
    with open(risk_pik) as f:
        out = cPickle.load(f)
    if output_key not in out:
        print 'key %s not found: availables %s' % (output_key, sorted(out))
        return
    loss_curve = out[output_key]
    plt = make_figure(output_key, loss_curve['losses'], loss_curve['poes'])
    plt.show()


parser = sap.Parser(plot_loss)
parser.arg('risk_pik', '.pik file containing the result of a computation')
parser.arg('output_key', 'an unique string for the output to plot')
