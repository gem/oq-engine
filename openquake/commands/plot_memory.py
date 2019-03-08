# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2019 GEM Foundation
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
from openquake.baselib import sap
from openquake.commonlib import util


def make_figure(plots):
    """
    :param plots: list of pairs (task_name, memory array)
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.grid(True)
    ax.set_xlabel('tasks')
    ax.set_ylabel('GB')
    start = 0
    for task_name, mem in plots:
        ax.plot(range(start, start + len(mem)), mem, label=task_name)
        start += len(mem)
    ax.legend()
    return plt


@sap.script
def plot_memory(calc_id=-1):
    """
    Plot the memory occupation
    """
    dstore = util.read(calc_id)
    plots = []
    for task_name in dstore['task_info']:
        mem = dstore['task_info/' + task_name]['mem_gb']
        plots.append((task_name, mem))
    plt = make_figure(plots)
    plt.show()


plot_memory.arg('calc_id', 'calculation ID', type=int)
