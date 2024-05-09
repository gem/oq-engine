# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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
import io
import os
import numpy
import json
import matplotlib as mpl
from scipy import interpolate
from openquake.hazardlib.calc.mean_rates import to_rates
from openquake.hazardlib.imt import from_string
from openquake.calculators.extract import get_info
from PIL import Image


def import_plt():
    if os.environ.get('TEXT'):
        import plotext as plt
    else:
        import matplotlib.pyplot as plt
    return plt


def _find_fact_maxC(T, code):
    # find the factor to convert to maximum component based on
    # ASCE7-16 and ASCE7-22

    f1 = interpolate.interp1d([0.2, 1], [1.1, 1.3])
    f2 = interpolate.interp1d([1, 5], [1.3, 1.5])
    f3 = interpolate.interp1d([0.2, 1], [1.2, 1.25])
    f4 = interpolate.interp1d([0.2, 1], [1.1, 1.3])

    if code == 'ASCE7-16':
        if T == 0:
            fact_maxC = 1.
        elif T <= 0.2:
            fact_maxC = 1.1
        elif T <= 1:
            fact_maxC = f1(T)
        elif T <= 5:
            fact_maxC = f2(T)
        else:
            fact_maxC = 1.5
    elif code == 'ASCE7-22':
        if T == 0:
            fact_maxC = 1.
        elif T <= 0.2:
            fact_maxC = 1.2
        elif T <= 1:
            fact_maxC = f3(T)
        elif T <= 10:
            fact_maxC = f4(T)
        else:
            fact_maxC = 1.5
    return fact_maxC


def _find_afe_target(imls, afe, sa_target):
    # find the target afe (or poe) for a given acceleration
    afe = numpy.clip(afe, 1E-45, numpy.inf)  # remove zeros
    f = interpolate.interp1d(numpy.log(imls), numpy.log(afe))
    afe_target = numpy.exp(f(numpy.log(sa_target)))
    return afe_target


def _get_label(imt):
    imtlab = imt if imt == 'PGA' else imt.replace(')', 's)')
    comp = 'Geom. mean' if imt == 'PGA' else 'Max. comp.'
    return imtlab + ' - ' + comp


def plot_mean_hcurves_rtgm(dstore, site_idx=0, plot_mce=False, 
                           update_dstore=False):
    """
    :param dstore: the datastore
    :returns: figure of hazard curves
    """
    dinfo = get_info(dstore)
    # get imls and imts, make arrays
    imtls = dinfo['imtls']
    # separate imts and imls
    AFE, afe_RTGM, imls = [], [], []
    imts = ['PGA', 'SA(0.2)', 'SA(1.0)']
    for imt in imts:
        # get periods and factors for converting btw geom mean and
        # maximum component
        T = from_string(imt).period
        f = 0 if imt == 0.0 else _find_fact_maxC(T, 'ASCE7-16')
        imls.append([im*f for im in imtls[imt]])
    # get rtgm ouptut from the datastore
    rtgm_df = dstore.read_df('rtgm', sel=dict(sid=site_idx))
    # get the IML for the 2475 RP
    rtgm_probmce = rtgm_df['ProbMCE']
    # get investigation time
    window = dinfo['investigation_time']
    # get hazard curves, put into rates
    mean_hcurve = dstore['hcurves-stats'][site_idx, 0]  # shape(M, L1)
    for m, hcurve in enumerate(mean_hcurve):
        AFE.append(to_rates(hcurve, window))
        # get the AFE of the iml that will be disaggregated for each IMT
        if rtgm_probmce[m] < imls[m][0]:
            afe_RTGM.append(0.0)
        else:
            afe_RTGM.append(_find_afe_target(imls[m], AFE[m], rtgm_probmce[m]))

    plt = import_plt()
    plt.figure(figsize=(12, 9))
    plt.rcParams.update({'font.size': 16})
    colors = mpl.colormaps['viridis'].reversed().resampled(3)
    patterns = ['-', '--', ':']
    for i, imt in enumerate(imts):
        lab = _get_label(imt)
        plt.loglog(imls[i], AFE[i], color=colors(i), linestyle=patterns[i],
                   label=lab, linewidth=3, zorder=1)
        
        if plot_mce:
        # plot the label only once but it must be at the end of the legend
            if imt == imts[-1]:
                plt.loglog([rtgm_probmce[i]], [afe_RTGM[i]], 'ko',
                           label='Probabilistic MCE',  linewidth=2,
                           markersize=10, zorder=3)
            else:
                plt.loglog([rtgm_probmce[i]], [afe_RTGM[i]], 'ko',
                           linewidth=2, markersize=10, zorder=3)
            plt.loglog([numpy.min(imls[i]), rtgm_probmce[i]],
                       [afe_RTGM[i], afe_RTGM[i]],
                       color='black', alpha=0.5, linestyle='--', linewidth=1.3)
        
            plt.loglog([rtgm_probmce[i], rtgm_probmce[i]],
                       [0, afe_RTGM[i]], color='black', alpha=0.5,
                       linestyle='--', linewidth=1.3)
    # add the ASCE 41-23 RPs
    plt.axhline(0.000404, color='red', linewidth=1.7, alpha=0.2, zorder=0)
    plt.axhline(0.002105, color='red', linewidth=1.7, alpha=0.2, zorder=0)
    plt.axhline(0.001025, color='red', linewidth=1.7, alpha=0.2, zorder=0)
    plt.axhline(0.004453, color='red', linewidth=1.7, alpha=0.2, zorder=0)
    plt.axhline(0.013767, color='red', linewidth=1.7, alpha=0.2, zorder=0)

    plt.text(0.0105, 0.000404*0.9, '2475 yr', fontsize='small', color='black', alpha=0.85 )
    plt.text(0.0105, 0.002105*0.9, '475 yr', fontsize='small', color='black', alpha=0.85 )
    plt.text(0.0105, 0.001025*0.9, '975 yr', fontsize='small', color='black', alpha=0.85)
    plt.text(0.0105, 0.004453*0.9, '225 yr', fontsize='small', color='black', alpha=0.85 )
    plt.text(0.0105, 0.013767*0.9, '72 yr', fontsize='small', color='black', alpha=0.85)

    # add note to see manual
    message = 'See WebUI User Guide for complete explanation of plot contents.'
    plt.text(0.0275, 0.00000186, message, fontsize='small', color='black', alpha=0.85 )

    # format plot
    plt.grid('both', alpha=0.6)
    plt.legend(fontsize=13)
    plt.xlabel('Acceleration (g)', fontsize=20)
    plt.ylabel('Annual frequency of exceedance', fontsize=20)
    plt.legend(loc="best", fontsize='16')
    plt.ylim([10E-6, 1.1])
    plt.xlim([0.01, 4])
    if update_dstore:
        bio = io.BytesIO()
        plt.savefig(bio, format='png', bbox_inches='tight')
        dstore['png/hcurves.png'] = Image.open(bio)
    return plt


def plot_governing_mce(dstore, site_idx=0, update_dstore=False):
    """
    :param dstore: the datastore
    :returns: image of governing MCE
    """
    dinfo = get_info(dstore)
    # get imls and imts, make arrays
    imtls = dinfo['imtls']
    plt = import_plt()
    js = dstore['asce07'][site_idx].decode('utf8')
    dic = json.loads(js)
    MCEr = [dic['PGA'], dic['Ss'], dic['S1']]
    T = [from_string(imt).period for imt in imtls]

    limit_det = [0.5, 1.5, 0.6]
    # presenting as maximum component -> do not need conversion facts
    rtgm = dstore.read_df('rtgm', sel=dict(sid=site_idx))
    if (rtgm.RTGM == 0).all():
        return
    rtgm_probmce = rtgm.ProbMCE.to_numpy()
    plt.figure(figsize=(8, 6))
    plt.rcParams.update({'font.size': 15})
    plt.plot(T, limit_det, 'kx', markersize=15, label='DLL', linewidth=1)
    plt.plot(T[0], rtgm_probmce[0], 'bX', markersize=12, label='$PGA_{2/50}$',
             linewidth=3)
    plt.plot(T[1:], rtgm_probmce[1:], 'bs', markersize=12,
             label='$S_{S,RT}$ and $S_{1,RT}$', linewidth=3)
    MCEr_det = [dic['PGA_84th'], dic['Ss_84th'], dic['S1_84th']]
    if any([val == 'n.a.' for val in MCEr_det]):  # hazard is lower than DLLs
        upperlim = max([rtgm_probmce[1], 1.5])
        plt.ylim([0, numpy.max([rtgm_probmce, MCEr, limit_det]) + 0.2])
    else:
        upperlim = max([rtgm_probmce[1], 1.5, MCEr_det[1]])
        plt.plot(T[0], MCEr_det[0], 'c^', markersize=10, label='$PGA_{84th}$',
                 linewidth=3)
        plt.plot(T[1:], MCEr_det[1:], 'cd', markersize=10,
                 label='$S_{S,84th}$ and $S_{1,84th}$', linewidth=3)
        plt.ylim(
            [0, numpy.max([rtgm_probmce,  MCEr, MCEr_det, limit_det]) + 0.2])
    plt.scatter(T[0], MCEr[0], s=200, label='Governing $MCE_G$',
                linewidth=2, facecolors='none', edgecolors='r')
    plt.scatter(T[1:], MCEr[1:], s=200, marker='s',
                label='Governing $MCE_R$', linewidth=2,
                facecolors='none', edgecolors='r')
    plt.grid('both')
    plt.ylabel('Spectral Acceleration (g)', fontsize=20)
    plt.xlabel('Period (s)', fontsize=20)
    plt.legend(loc="upper right", fontsize='13')
    plt.xlim([-0.02, 1.2])

    # add user guide message
    message = 'See WebUI User Guide for complete explanation of plot contents.'
    plt.text(0.03, -upperlim*0.22, message, fontsize='small', color='black',
             alpha=0.85)

    if update_dstore:
        bio = io.BytesIO()
        plt.savefig(bio, format='png', bbox_inches='tight')
        dstore['png/governing_mce.png'] = Image.open(bio)
    return plt


def _plot(ax, ax1, site_idx, m, imls, imls_o,
          mrs, rtgm_probmce, afe_target, fact):
    out_contr_all = {}
    for i, src in enumerate(mrs.src_id):
        # get contribution at target level for that source
        afes = mrs[site_idx, m, :, i]
        if (afes == 0).all():
            continue
        afe_uhgm = _find_afe_target(
            imls, numpy.clip(afes, 1E-15, numpy.inf), rtgm_probmce[m])
        # get % contribution of that source
        contr_source = afe_uhgm / afe_target
        out_contr_all[i] = contr_source * 100

    # identify contribution of largest contributor, make color scale
    largest_contr = max(out_contr_all.values())
    sample = sum(val > fact*largest_contr
                 for val in out_contr_all.values())
    viridis = mpl.colormaps['viridis'].reversed().resampled(sample)

    # find and plot the sources, highlighting the ones that contribute more
    # than 10% of largest contributor
    # use j to only add the "other sources" label once
    # use i to cycle through the colors for the major source contributors
    i = j = 0
    for ind in out_contr_all:
        afes = mrs[site_idx, m, :, ind]
        # if it's not a big contributor, plot in silver
        if out_contr_all[ind] <= fact * largest_contr:
            if j == 0:
                ax[m].loglog(imls, afes, 'silver', linewidth=0.7,
                             label='other sources')
                ax1.loglog(imls_o, afes, 'silver', linewidth=0.7,
                           label='other source')
                j += 1
            else:
                ax[m].loglog(imls, afes, 'silver', linewidth=0.7)
                ax1.loglog(imls_o, afes, 'silver', linewidth=0.7)
        # if it is, plot in color
        else:
            ax[m].loglog(imls, afes, c=viridis(i),
                         label=str(mrs.src_id[ind]))
            ax1.loglog(imls_o, afes, c=viridis(i),
                       label=str(mrs.src_id[ind]))
            i += 1


def _plot_m(plt, ax, m, imt, AFE, fact, imtls, site_idx, rtgm_probmce,
                mrs, update_dstore, dstore):
    # identify the sources that have a contribution > than fact (here 10%) of
    # the largest contributor;
    fig1, ax1 = plt.subplots()

    # annual frequency of exceedance:
    T = from_string(imt).period
    f = 0 if imt == 0.0 else _find_fact_maxC(T, 'ASCE7-16')
    imls_o = imtls[imt]
    imls = numpy.array([iml*f for iml in imls_o])
    # have to compute everything for max comp. and for geom. mean
    RTGM = rtgm_probmce[m]
    RTGM_o = rtgm_probmce[m] / f
    afe_target = _find_afe_target(imls, AFE[m], RTGM)
    afe_target_o = _find_afe_target(imls_o, AFE[m], RTGM_o)

    # populate 3-panel plot
    ax[m].loglog(imls, AFE[m], 'k', label=_get_label(imt),
                 linewidth=2, zorder=3)
    ax[m].loglog([numpy.min(imls), RTGM], [afe_target, afe_target], 'k--',
                 linewidth=2, zorder=3)
    ax[m].loglog([RTGM, RTGM], [0, afe_target], 'k--', linewidth=2,
                 zorder=3)
    ax[m].loglog([RTGM], [afe_target], 'ko', label='Probabilistic MCE',
                 linewidth=2, zorder=3)
    # populate individual plots
    ax1.loglog(imls_o, AFE[m], 'k', label=imt + ' - Geom. mean',
               linewidth=2, zorder=3)
    ax1.loglog([numpy.min(imls_o), RTGM_o], [afe_target_o, afe_target_o],
               'k--', linewidth=2, zorder=3)
    ax1.loglog([RTGM_o, RTGM_o], [0, afe_target_o], 'k--', linewidth=2,
               zorder=3)
    ax1.loglog([RTGM_o], [afe_target_o], 'ko', label='Probabilistic MCE',
               linewidth=2, zorder=3)
    _plot(ax, ax1, site_idx, m, imls, imls_o,
          mrs, rtgm_probmce, afe_target, fact)

    # populate subplot - maximum component
    ax[m].grid('both')
    ax[m].set_xlabel(imt+' (g)', fontsize=16)
    ax[m].set_ylabel('Annual Freq. Exceedance', fontsize=16)
    ax[m].legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='13')
    ax[m].set_ylim([10E-6, 1.1])
    ax[m].set_xlim([0.01, 4])

    # add user guide message
    if m == 2:
        message = ('See WebUI User Guide for complete explanation '
                   'of plot contents.')
        ax[m].text(0.0105, 0.000000506, message, fontsize='small',
                   color='black', alpha=0.85 ) 

    # populate single imt plots - geometric mean
    ax1.grid('both')
    ax1.set_xlabel(imt+' (g)', fontsize=16)
    ax1.set_ylabel('Annual Freq. Exceedance', fontsize=16)
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='13')
    ax1.set_ylim([10E-6, 1.1])
    ax1.set_xlim([0.01, 4])

    if update_dstore:
        # save single imt plot
        bio1 = io.BytesIO()
        fig1.savefig(bio1, format='png', bbox_inches='tight')
        # keep these in webui until we finish checks and have a command
        # line exporter, then we can change the name to _{imt} and they
        # will not appear in the webui
        dstore[f'png/disagg_by_src-{imt}.png'] = Image.open(bio1)
    fig1.tight_layout()


def plot_disagg_by_src(dstore, site_idx=0, update_dstore=False):
    dinfo = get_info(dstore)
    # get imls and imts, make arrays
    imtls = dinfo['imtls']
    # get rtgm ouptut from the datastore
    rtgm_df = dstore.read_df('rtgm', sel=dict(sid=site_idx))
    if (rtgm_df.RTGM == 0).all():
        return

    # get hazard curves, put into rates
    AFE = []
    mean_hcurve = dstore['hcurves-stats'][site_idx, 0]  # shape(M, L1)
    window = dinfo['investigation_time']
    for m, hcurve in enumerate(mean_hcurve):
        AFE.append(to_rates(hcurve, window))

    plt = import_plt()
    fig, ax = plt.subplots(3, figsize=(8, 15))
    fact=0.1
    for m, imt in enumerate(imtls):
        _plot_m(plt, ax, m, imt, AFE, fact, imtls, site_idx, rtgm_df['ProbMCE'],
                dstore['mean_rates_by_src'], update_dstore, dstore)
    if update_dstore:
        # save triple plot
        bio = io.BytesIO()
        fig.savefig(bio, format='png', bbox_inches='tight')
        dstore['png/disagg_by_src-All-IMTs.png'] = Image.open(bio)
    fig.tight_layout()
    return plt
