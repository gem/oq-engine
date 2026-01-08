#
# --------------- POINT - Propagation Of epIstemic uNcerTainty ----------------
# Copyright (C) 2025-2026 GEM Foundation
#
#                `.......      `....     `..`...     `..`... `......
#                `..    `..  `..    `..  `..`. `..   `..     `..
#                `..    `..`..        `..`..`.. `..  `..     `..
#                `.......  `..        `..`..`..  `.. `..     `..
#                `..       `..        `..`..`..   `. `..     `..
#                `..         `..     `.. `..`..    `. ..     `..
#                `..           `....     `..`..      `..     `..
#
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# coding: utf-8

import re
import os
import copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from openquake.commonlib import datastore


def plot_dsg_md_prepare(dstore_name, imt_id, poe_id, site_id):

    dstore = datastore.read(dstore_name)
    oqp = dstore.get('oqparam', None)
    imts = list(oqp.imtls)

    if 'site_model' in oqp.inputs:
        sites = pd.read_csv(oqp.inputs['site_model'][0])
        site_cond = 'soil'
    else:
        sites = pd.read_csv(oqp.inputs['sites'])
        site_cond = 'rock'

    # Size of the disaggregation matrix:
    # 0 - Number of sites
    # 1 - Number of IMTs
    # 2 - Number of poes
    # 3 - Number of magnitude bins
    # 4 - Number of distance bins
    # 5 - Number of realisations
    dmtx = dstore['disagg-stats']['Mag_Dist'][:]

    # weights = dstore.get('weights', None)[:]
    # mean_dsg = np.average(dmtx[site_id, :, :, imt_id, poe_id, 0], axis=2,
    #                       weights=weights)
    mean_dsg = dmtx[site_id, :, :, imt_id, poe_id, 0]
    mean_dsg.shape

    ma_bins = dstore.get('disagg-bins/Mag', None)[:]
    dist_bins = dstore.get('disagg-bins/Dist', None)[:]
    ma_cen = ma_bins[:-1] + np.diff(ma_bins) / 2
    dist_cen = dist_bins[:-1] + np.diff(dist_bins) / 2

    # Compute RP
    rp = int(np.round(1 / -(np.log(1-oqp.poes_disagg[poe_id])), 0))

    conf = {}
    conf['site_lab'] = sites['custom_site_id'][site_id]
    conf['imt_lab'] = imts[imt_id]
    conf['return_period'] = rp
    conf['site_condition'] = site_cond

    return dist_cen, ma_cen, mean_dsg, conf


def plot_dsg_md(dist_cen, ma_cen, dsg_mea, conf):
    """
    :param dist_cen:
    :param ma_cen:
    """

    mean_dsg = copy.deepcopy(dsg_mea)

    # Configuration parameters
    imt_lab = conf.get('imt_lab')
    site_lab = conf.get('site_lab')
    calc_id = conf.get('calc_id')
    outfolder = conf.get('figure_folder')
    rp = conf.get('return_period')
    site_cond = conf.get('site_condition')

    # Create meshes
    dist_g, ma_g = np.meshgrid(dist_cen, ma_cen)

    fig, axs = plt.subplots(1, 1)
    fig.set_size_inches(7, 5)
    mpl.rc('image', cmap='YlGnBu')

    plt.pcolormesh(dist_g, ma_g, mean_dsg)

    aa = copy.deepcopy(mean_dsg)
    tidx = np.isnan(mean_dsg)
    if np.sum(tidx):
        aa[tidx] = 0.0
        idx = np.argmax(aa)
    else:
        idx = np.argmax(mean_dsg)
    idx = np.unravel_index(idx, mean_dsg.shape)

    plt.plot(dist_g[idx], ma_g[idx], 'x', mfc='none', mec='red', mew=2)
    label = f'(R:{dist_g[idx]:.1f} km, M:{ma_g[idx]:.2f}): {mean_dsg[idx]:.2e}'

    bbox = dict(boxstyle="round", fc="white")
    axs.text(0.98, 0.97, label, transform=axs.transAxes,
             fontsize=9, va='top', ha='right', bbox=bbox)
    plt.colorbar()

    ylim = axs.get_ylim()
    plt.xlim([0, 100])
    plt.ylim([ylim[0], 8.0])
    plt.xlabel('Distance, Rrup [km]')
    plt.ylabel('Magnitude, M ')
    plt.grid(which='major', ls='--', color='gray')
    plt.title(f"Site: {site_lab} | IMT:{imt_lab} | RP:{rp} yr")

    tmp = re.sub('\\.', 'pt', imt_lab)
    tmp = re.sub('\\(', '-', tmp)
    tmp = re.sub('\\)', '', tmp)

    sid = re.sub('_', '-', site_lab)
    if 'fig_name' in conf:
        fname = conf.get('fig_name')
    else:
        fname = f"dsg_{calc_id}_{sid}_{tmp.lower()}_rp{rp}_{site_cond}.png"
    fname = os.path.join(outfolder, fname)
    plt.savefig(fname)

    print(f'Output figure : {fname}')
    print(f'Mag range     : {ma_g[idx]-0.4:.2f} - {ma_g[idx]+0.4:.2f}')

    return [ma_g[idx], dist_g[idx], site_cond]
