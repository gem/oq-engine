# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2025 GEM Foundation
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
import matplotlib as mpl
from scipy import interpolate
from openquake.hazardlib.calc.mean_rates import to_rates
from openquake.hazardlib.imt import from_string
from openquake.calculators.extract import get_info
from PIL import Image

ASCE_version = 'ASCE7-22'


def import_plt():
    if os.environ.get('TEXT'):
        import plotext as plt
    else:
        import matplotlib.pyplot as plt
    return plt


def _convert_imt(imt):
    # Convert the imt string from USGS format, for instance SA1P1 -> SA(1.1)
    if imt == "PGA":
        IMT = "PGA"
    else:
        IMT = imt.replace("SA", 'SA(').replace('P', '.') + ')'
    return (IMT)


def _find_fact_maxC(T, ASCE_version):
    # find the factor to convert to maximum component based on
    # ASCE7-16 and ASCE7-22

    if ASCE_version == 'ASCE7-16':
        if T == 0:
            fact_maxC = 1.
        elif T <= 0.2:
            fact_maxC = 1.1
        elif T <= 1:
            fact_maxC = numpy.interp(T, [0.2, 1], [1.1, 1.3])
        elif T <= 5:
            fact_maxC = numpy.interp(T, [1, 5], [1.3, 1.5])
        else:
            fact_maxC = 1.5
    elif ASCE_version == 'ASCE7-22':
        if T <= 0.2:
            fact_maxC = 1.2
        elif T <= 1:
            fact_maxC = numpy.interp(T, [0.2, 1], [1.2, 1.25])
        elif T <= 10:
            fact_maxC = numpy.interp(T, [1, 10], [1.25, 1.3])
        else:
            fact_maxC = 1.5
    return numpy.round(fact_maxC, 3)


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


def _hcurves(imts, plot_imt, plot_IMT, AFE, afe_RTGM, imls, imls_mc, imtls,
             rtgm_df, plot_rtgm_probmce, site_idx, dinfo, dstore):
    for imt in plot_imt:
        # convert imts from USGS format
        IMT = _convert_imt(imt)
        plot_IMT.append(IMT)
        idx = imts.index[imts == imt]
        # get periods and factors for converting btw geom mean and
        # maximum component
        T = from_string(IMT).period
        f = 1 if imt == "PGA" else _find_fact_maxC(T, ASCE_version)
        imls.append([im for im in imtls[IMT]])
        imls_mc.append([im*f for im in imtls[IMT]])
        # get the IML for the 2475 RP
        rtgm_probmce = rtgm_df['ProbMCE']
        plot_rtgm_probmce.append(rtgm_probmce[idx])
        # get investigation time
        window = dinfo['investigation_time']
        # get hazard curves, put into rates
        mean_hcurve = dstore['hcurves-stats'][site_idx, 0][idx]  # shape(M, L1)
        for m, hcurve in enumerate(mean_hcurve):
            AFE.append(to_rates(hcurve, window))
            # get the AFE of the iml that will be disaggregated for each IMT
            if rtgm_probmce[m] < imls[m][0]:
                afe_RTGM.append(0.0)
            else:
                afe_RTGM.append(_find_afe_target(imls[m], AFE[m],
                                                 rtgm_probmce[m]))


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
    AFE, afe_RTGM, imls, imls_mc = [], [], [], []
    # get rtgm ouptut from the datastore
    rtgm_df = dstore.read_df('rtgm', sel=dict(sid=site_idx))
    imts = rtgm_df['IMT']
    plot_rtgm_probmce = []
    # specify subset of imts to plot
    imt_sub = ['PGA', 'SA0P2', 'SA1P0', 'SA2P0', 'SA5P0']
    plot_imt = [i for i in imts if i in imt_sub]
    plot_IMT = []

    plt = import_plt()
    plt.figure(figsize=(12, 9))
    plt.rcParams.update({'font.size': 16})
    colors = mpl.colormaps['viridis'].reversed().resampled(5)
    patterns = ['-', '-.', '--', ':', '-.']

    _hcurves(imts, plot_imt, plot_IMT, AFE, afe_RTGM, imls, imls_mc, imtls,
             rtgm_df, plot_rtgm_probmce, site_idx, dinfo, dstore)

    if plot_mce:
        for i, imt in enumerate(plot_imt):
            plt.loglog(imls_mc[i], AFE[i], color=colors(i),
                       label=plot_IMT[i], linewidth=3, zorder=1,
                       linestyle=patterns[i])
        # plot the label only once but it must be at the end of the legend
            if imt == plot_imt[-1]:
                plt.loglog([plot_rtgm_probmce[i]], [afe_RTGM[i]], 'ko',
                           label='Probabilistic MCE',  linewidth=2,
                           markersize=10, zorder=3)
            else:
                plt.loglog([plot_rtgm_probmce[i]], [afe_RTGM[i]], 'ko',
                           linewidth=2, markersize=10, zorder=3)
            plt.loglog([(plot_rtgm_probmce[i]-1000), plot_rtgm_probmce[i]],
                       [afe_RTGM[i], afe_RTGM[i]],
                       color='black', alpha=0.5, linestyle='--', linewidth=1.3)

            plt.loglog([plot_rtgm_probmce[i], plot_rtgm_probmce[i]],
                       [0, afe_RTGM[i]], color='black', alpha=0.5,
                       linestyle='--', linewidth=1.3)
    else:
        for i, imt in enumerate(plot_imt):
            plt.loglog(imls[i], AFE[i], color=colors(i),
                       label=plot_IMT[i], linewidth=3, zorder=1,
                       linestyle=patterns[i])

    # add the ASCE 41-23 RPs
    plt.axhline(0.000404, color='red', linewidth=1.7, alpha=0.2, zorder=0)
    plt.axhline(0.002105, color='red', linewidth=1.7, alpha=0.2, zorder=0)
    plt.axhline(0.001025, color='red', linewidth=1.7, alpha=0.2, zorder=0)
    plt.axhline(0.004453, color='red', linewidth=1.7, alpha=0.2, zorder=0)
    plt.axhline(0.013767, color='red', linewidth=1.7, alpha=0.2, zorder=0)

    plt.text(0.0105, 0.000404*0.9, '2475 yr', fontsize='small', color='black',
             alpha=0.85)
    plt.text(0.0105, 0.002105*0.9, '475 yr', fontsize='small', color='black',
             alpha=0.85)
    plt.text(0.0105, 0.001025*0.9, '975 yr', fontsize='small', color='black',
             alpha=0.85)
    plt.text(0.0105, 0.004453*0.9, '225 yr', fontsize='small', color='black',
             alpha=0.85)
    plt.text(0.0105, 0.013767*0.9, '72 yr', fontsize='small', color='black',
             alpha=0.85)

    # add note to see manual
    message = 'See WebUI User Guide for complete explanation of plot contents.'
    plt.text(0.0275, 0.00000186, message, fontsize='small', color='black',
             alpha=0.85)

    # format plot
    plt.grid('both', alpha=0.6)
    plt.legend(fontsize=13)
    plt.xlabel('Acceleration (g)', fontsize=20)
    plt.ylabel('Annual frequency of exceedance', fontsize=20)
    plt.legend(loc="best", fontsize='16')
    plt.ylim([10E-6, 1.1])
    plt.xlim([0.01, 2])
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
    plt = import_plt()
    _fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 15))
    # get imls and imts, make arrays
    mce_df = dstore.read_df('mce', sel=dict(sid=site_idx))
    det_mce = mce_df['DetMCE']
    mce = mce_df['MCE']
    prob_mce = mce_df['ProbMCE']
    imts = mce_df['IMT']
    T = [from_string(imt).period for imt in imts]
    DLL = mce_df['DLL']
    ax1.plot(T[1:], DLL[1:], 'kx', markersize=8, label='DLL', linewidth=1,
             linestyle='-')
    ax1.plot(T[1:], prob_mce[1:], 'bX', markersize=8, label='Probabilisitc $MCE_r$',
             linewidth=1, linestyle='-')
    upperlim = max(max(prob_mce), max(mce), max(det_mce), max(DLL))
    ax1.plot(T[1:], det_mce[1:], 'c^', markersize=8, label='Deterministic $MCE_r$',
             linewidth=1, linestyle='-')
    ax1.set_ylim([0.01, upperlim + 0.2])
    ax1.plot(T[1:], mce[1:], 'r', label='Governing $MCE_r$', linewidth=4, linestyle=':')
    ax1.grid('both')
    ax1.set_ylabel('Spectral Acceleration (g)', fontsize=20)
    ax1.set_xlabel('Period (s)', fontsize=20)
    ax1.legend(loc="lower left", fontsize='13')
    ax1.set_xlim([min(T[1:]), max(T)])

    plt.rcParams.update({'font.size': 15})
    ax2.plot(T[1:], DLL[1:], 'kx', markersize=8, label='DLL', linewidth=1,
             linestyle='-')
    ax2.plot(T[1:], prob_mce[1:], 'bX', markersize=8, label='Probabilisitc $MCE_r$',
             linewidth=1, linestyle='-')
    ax2.plot(T[1:], det_mce[1:], 'c^', markersize=8, label='Deterministic $MCE_r$',
             linewidth=1, linestyle='-')
    plt.ylim([0.01, upperlim + 0.2])
    ax2.plot(T[1:], mce[1:], 'r', label='Governing $MCE_r$', linewidth=4, linestyle=':')
    ax2.grid('both')
    ax2.set_ylabel('Spectral Acceleration (g)', fontsize=20)
    ax2.set_xlabel('Period (s)', fontsize=20)
    ax2.legend(loc="upper right", fontsize='13')
    ax2.set_xlim([0, 2.0])
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax2.set_xscale('linear')
    ax2.set_yscale('linear')

    # add user guide message
    message = 'See WebUI User Guide for complete explanation of plot contents.'
    plt.text(0.03, -upperlim*0.2, message, fontsize='small', color='black',
             alpha=0.85)
    if update_dstore:
        bio = io.BytesIO()
        plt.savefig(bio, format='png', bbox_inches='tight')
        dstore['png/governing_mce.png'] = Image.open(bio)
    return plt


def _plot(ax, ax1, site_idx, plot_idx, m, n, imls, imls_o,
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
                if m in plot_idx:
                    ax[n].loglog(imls, afes, 'silver', linewidth=0.7,
                                 label='other sources')
                ax1.loglog(imls_o, afes, 'silver', linewidth=0.7,
                           label='other source')
                j += 1
            else:
                if m in plot_idx:
                    ax[n].loglog(imls, afes, 'silver', linewidth=0.7)
                ax1.loglog(imls_o, afes, 'silver', linewidth=0.7)
        # if it is, plot in color
        else:
            if m in plot_idx:
                ax[n].loglog(imls, afes, c=viridis(i),
                             label=str(mrs.src_id[ind]))
            ax1.loglog(imls_o, afes, c=viridis(i), label=str(mrs.src_id[ind]))
            i += 1


def _plot_m(plt, plot_idx, ax, m, n, imt, AFE, fact, imtls, site_idx,
            rtgm_probmce, mrs, update_dstore, dstore):
    # identify the sources that have a contribution > than fact (here 10%) of
    # the largest contributor;
    fig1, ax1 = plt.subplots()
    # annual frequency of exceedance:
    T = from_string(imt).period
    f = 1 if imt == "PGA" else _find_fact_maxC(T, ASCE_version)
    imls_o = imtls[imt]
    imls = numpy.array([iml*f for iml in imls_o])
    # have to compute everything for max comp. and for geom. mean
    RTGM = rtgm_probmce[m]
    RTGM_o = rtgm_probmce[m] / f
    afe_target = _find_afe_target(imls, AFE[m], RTGM)
    afe_target_o = _find_afe_target(imls_o, AFE[m], RTGM_o)

    # populate 3-panel plot
    if m in plot_idx:
        ax[n].loglog(imls, AFE[m], 'k', label=_get_label(imt),
                     linewidth=2, zorder=3)
        ax[n].loglog([numpy.min(imls), RTGM], [afe_target, afe_target], 'k--',
                     linewidth=2, zorder=3)
        ax[n].loglog([RTGM, RTGM], [0, afe_target], 'k--', linewidth=2,
                     zorder=3)
        ax[n].loglog([RTGM], [afe_target], 'ko', label='Probabilistic MCE',
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
    _plot(ax, ax1, site_idx, plot_idx, m, n, imls, imls_o,
          mrs, rtgm_probmce, afe_target, fact)

    # populate subplot - maximum component
    if m in plot_idx:
        ax[n].grid('both')
        ax[n].set_xlabel(imt+' (g)', fontsize=16)
        ax[n].set_ylabel('Annual Freq. Exceedance', fontsize=16)
        ax[n].legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='13')
        ax[n].set_ylim([10E-6, 1.1])
        ax[n].set_xlim([0.01, 5])

    # add user guide message
    if m == 2:
        message = ('See WebUI User Guide for complete explanation '
                   'of plot contents.')
        ax[m].text(0.0105, 0.000000506, message, fontsize='small',
                   color='black', alpha=0.85)

    # populate single imt plots - geometric mean
    ax1.grid('both')
    ax1.set_xlabel(imt+' (g)', fontsize=16)
    ax1.set_ylabel('Annual Freq. Exceedance', fontsize=16)
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='13')
    ax1.set_ylim([10E-6, 1.1])
    ax1.set_xlim([0.01, 5])
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
    imts = list(imtls)
    plot_idx = [imts.index('PGA'), imts.index('SA(0.2)'),
                imts.index('SA(1.0)')]
    n = 0
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
    fact = 0.1
    for m, imt in enumerate(imtls):
        if rtgm_df['ProbMCE'][m] == 0:
            continue
        _plot_m(plt, plot_idx, ax, m, n, imt, AFE, fact, imtls, site_idx,
                rtgm_df['ProbMCE'], dstore['mean_rates_by_src'], update_dstore,
                dstore)
        if m in plot_idx:
            n = n+1
    if update_dstore:
        # save triple plot
        bio = io.BytesIO()
        fig.savefig(bio, format='png', bbox_inches='tight')
        dstore['png/disagg_by_src-All-IMTs.png'] = Image.open(bio)
    fig.tight_layout()
    return plt
