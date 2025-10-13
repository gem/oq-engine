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
import json
import matplotlib as mpl
from scipy import interpolate
from openquake.commonlib import readinput
from openquake.hazardlib.calc.mean_rates import to_rates
from openquake.hazardlib.imt import from_string
from openquake.calculators.extract import get_info
from openquake.calculators.postproc.plots import (
    add_borders, adjust_limits, auto_limits)
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
             rtgm_df, plot_rtgm_probmce, sid, dinfo, dstore):
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
        mean_hcurve = dstore['hcurves-stats'][sid, 0][idx]  # shape(M, L1)
        for m, hcurve in enumerate(mean_hcurve):
            AFE.append(to_rates(hcurve, window))
            # get the AFE of the iml that will be disaggregated for each IMT
            if rtgm_probmce[m] < imls[m][0]:
                afe_RTGM.append(0.0)
            else:
                afe_RTGM.append(_find_afe_target(imls[m], AFE[m], rtgm_probmce[m]))


# NOTE: there are no occurrences in the engine calling this function with plot_mce=True
def plot_mean_hcurves_rtgm(dstore, sid=0, plot_mce=False, axes=None):
    """
    Plot mean hazard curves

    :param dstore: the datastore
    :param sid: site index
    :param plot_mce: whether to show MCE RTGM points
    :param axes: optional matplotlib axes to draw on
    :returns: figure of hazard curves
    """
    plt = import_plt()

    dinfo = get_info(dstore)
    # get imls and imts, make arrays
    imtls = dinfo['imtls']
    # separate imts and imls
    AFE, afe_RTGM, imls, imls_mc = [], [], [], []
    # get rtgm ouptut from the datastore
    rtgm_df = dstore.read_df('rtgm', sel=dict(sid=sid))
    imts = rtgm_df['IMT']
    plot_rtgm_probmce = []
    # specify subset of imts to plot
    imt_sub = ['PGA', 'SA0P2', 'SA1P0', 'SA2P0', 'SA5P0']
    plot_imt = [i for i in imts if i in imt_sub]
    plot_IMT = []

    # Always ensure axes exists
    own_fig = axes is None
    if own_fig:
        fig, axes = plt.subplots(figsize=(12, 9))

    plt.rcParams.update({'font.size': 16})
    colors = plt.get_cmap('viridis_r', 5)
    patterns = ['-', '-.', '--', ':', '-.']

    _hcurves(imts, plot_imt, plot_IMT, AFE, afe_RTGM, imls, imls_mc, imtls,
             rtgm_df, plot_rtgm_probmce, sid, dinfo, dstore)

    if plot_mce:
        for i, imt in enumerate(plot_imt):
            axes.loglog(imls_mc[i], AFE[i], color=colors(i),
                        label=plot_IMT[i], linewidth=3, zorder=1,
                        linestyle=patterns[i])
        # plot the label only once but it must be at the end of the legend
            if imt == plot_imt[-1]:
                axes.loglog([plot_rtgm_probmce[i]], [afe_RTGM[i]], 'ko',
                            label='Probabilistic MCE',  linewidth=2,
                            markersize=10, zorder=3)
            else:
                axes.loglog([plot_rtgm_probmce[i]], [afe_RTGM[i]], 'ko',
                            linewidth=2, markersize=10, zorder=3)
            axes.loglog([(plot_rtgm_probmce[i]-1000), plot_rtgm_probmce[i]],
                        [afe_RTGM[i], afe_RTGM[i]],
                        color='black', alpha=0.5, linestyle='--', linewidth=1.3)

            axes.loglog([plot_rtgm_probmce[i], plot_rtgm_probmce[i]],
                        [0, afe_RTGM[i]], color='black', alpha=0.5,
                        linestyle='--', linewidth=1.3)
    else:
        for i, imt in enumerate(plot_imt):
            axes.loglog(imls[i], AFE[i], color=colors(i),
                        label=plot_IMT[i], linewidth=3, zorder=1,
                        linestyle=patterns[i])

    # add the ASCE 41-23 RPs
    for afe_val, label in [
        (0.000404, '2475 yr'),
        (0.002105, '475 yr'),
        (0.001025, '975 yr'),
        (0.004453, '225 yr'),
        (0.013767, '72 yr'),
    ]:
        axes.axhline(afe_val, color='red', linewidth=1.7, alpha=0.2, zorder=0)
        axes.text(0.0105, afe_val * 0.9, label, fontsize='small', color='black',
                  alpha=0.85)

    axes.grid('both', alpha=0.6)
    axes.set_xlabel('Acceleration (g)', fontsize=13)
    axes.set_ylabel('Annual frequency of exceedance', fontsize=13)
    axes.legend(fontsize=11, loc='best')
    axes.set_ylim([10E-6, 1.1])
    axes.set_xlim([0.01, 2])
    axes.set_yscale('log')
    axes.set_xscale('log')

    return plt


def plot_governing_mce_asce_7_16(dstore, site_idx=0, update_dstore=False):
    """
    :param dstore: the datastore
    :returns: image of governing MCE
    """
    dinfo = get_info(dstore)
    # get imls and imts, make arrays
    imtls = dinfo['imtls']
    plt = import_plt()
    MCEr = dstore.read_df('mce_governing').SaM.to_numpy()
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

    plt.scatter(T[0], MCEr[0], s=200, label='Governing $MCE_G$',
                linewidth=2, facecolors='none', edgecolors='r')
    plt.scatter(T[1:], MCEr[1:], s=200, marker='s',
                label='Governing $MCE_R$', linewidth=2,
                facecolors='none', edgecolors='r')
    plt.grid('both')
    plt.ylabel('Spectral Acceleration (g)', fontsize=13)
    plt.xlabel('Period (s)', fontsize=13)
    plt.legend(loc="upper right", fontsize='11')
    plt.xlim([-0.02, 1.2])

    # add user guide message
    # FIXME: the message is not being displayed
    message = 'See WebUI User Guide for complete explanation of plot contents.'
    # plt.text(0.03, -upperlim*0.22, message, fontsize='small', color='black', alpha=0.85)

    if update_dstore:
        bio = io.BytesIO()
        plt.savefig(bio, format='png', bbox_inches='tight')
        dstore['png/mce.png'] = Image.open(bio)
    return plt


def plot_mce_spectra(dstore, site_idx=0, update_dstore=False):
    """
    :param dstore: the datastore
    :returns: image of MCE spectra
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
    ax1.plot(T[1:], prob_mce[1:], 'bX', markersize=8,
             label='Probabilisitc $MCE_r$',
             linewidth=1, linestyle='-')
    upperlim = max(max(prob_mce), max(mce), max(det_mce), max(DLL))
    ax1.plot(T[1:], det_mce[1:], 'c^', markersize=8,
             label='Deterministic $MCE_r$',
             linewidth=1, linestyle='-')
    ax1.set_ylim([0.01, upperlim + 0.2])
    ax1.plot(T[1:], mce[1:], 'r', label='Governing $MCE_r$',
             linewidth=4, linestyle=':')
    ax1.grid(which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    ax1.minorticks_on()
    ax1.set_ylabel('Spectral Acceleration (g)', fontsize=13)
    ax1.set_xlabel('Period (s)', fontsize=13)
    ax1.legend(loc="lower left", fontsize='11')
    ax1.set_xlim([min(T[1:]), max(T)])

    plt.rcParams.update({'font.size': 15})
    ax2.plot(T[1:], DLL[1:], 'kx', markersize=8, label='DLL', linewidth=1,
             linestyle='-')
    ax2.plot(T[1:], prob_mce[1:], 'bX', markersize=8,
             label='Probabilisitc $MCE_r$',
             linewidth=1, linestyle='-')
    ax2.plot(T[1:], det_mce[1:], 'c^', markersize=8,
             label='Deterministic $MCE_r$',
             linewidth=1, linestyle='-')
    plt.ylim([0.01, upperlim + 0.2])
    ax2.plot(T[1:], mce[1:], 'r', label='Governing $MCE_r$',
             linewidth=4, linestyle=':')
    ax2.grid('both')
    ax2.set_ylabel('Spectral Acceleration (g)', fontsize=13)
    ax2.set_xlabel('Period (s)', fontsize=13)
    ax2.legend(loc="upper right", fontsize='11')
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
        dstore['png/mce_spectra.png'] = Image.open(bio)
    return plt


def plot_governing_mce(dstore, update_dstore=False):
    """
    :param dstore: the datastore
    :returns: image of governing MCE (log-log plot)
    """
    plt = import_plt()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 15))
    plt.subplots_adjust(bottom=0.1)

    governing_mce_df = dstore.read_df('mce_governing')
    governing_mce_period = governing_mce_df['period']
    # governing_mce_sam = governing_mce_df['SaM']
    mce = governing_mce_df['SaM']

    ax1.plot(governing_mce_period[1:], mce[1:], 'black',
             label='Governing $MCE_r$', linewidth=2, linestyle='-')

    ax1.set_xscale('log')
    ax1.set_yscale('log')

    ax1.set_ylabel('Spectral Acceleration (g)', fontsize=13)
    ax1.set_xlabel('Period (s)', fontsize=13)
    ax1.legend(loc="lower left", fontsize=11)
    ax1.grid(which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    ax1.minorticks_on()

    plt.rcParams.update({'font.size': 15})

    ax2.plot(governing_mce_period[1:], mce[1:], 'black',
             label='Governing $MCE_r$', linewidth=2, linestyle='-')
    # plt.ylim([0.01, upperlim + 0.2])
    ax2.grid('both')
    ax2.set_ylabel('Spectral Acceleration (g)', fontsize=13)
    ax2.set_xlabel('Period (s)', fontsize=13)
    ax2.legend(loc="lower left", fontsize='11')
    ax2.set_xlim([0, 2.0])
    ax2.set_xscale('linear')
    ax2.set_yscale('linear')

    # add user guide message as a footer, centered below the x-axis
    message = 'See WebUI User Guide for complete explanation of plot contents.'
    fig.text(
        0.5, 0.01,   # x=0.5 centers horizontally
        message,
        ha='center', va='bottom',
        fontsize='small', color='black', alpha=0.85
    )

    if update_dstore:
        bio = io.BytesIO()
        plt.savefig(bio, format='png', bbox_inches='tight')
        dstore['png/governing_mce.png'] = Image.open(bio)

    return plt


def _plot(ax, ax1, sid, plot_idx, m, n, imls, imls_o,
          mrs, rtgm_probmce, afe_target, fact):
    out_contr_all = {}
    for i, src in enumerate(mrs.src_id):
        # get contribution at target level for that source
        afes = mrs[sid, m, :, i]
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
        afes = mrs[sid, m, :, ind]
        # if it's not a big contributor, plot in silver
        if out_contr_all[ind] <= fact * largest_contr:
            if j == 0:
                if m in plot_idx:
                    ax[n].loglog(imls, afes, 'silver', linewidth=0.7,
                                 label='other sources')
                if ax1 is not None:
                    ax1.loglog(imls_o, afes, 'silver', linewidth=0.7,
                               label='other source')
                j += 1
            else:
                if m in plot_idx:
                    ax[n].loglog(imls, afes, 'silver', linewidth=0.7)
                if ax1 is not None:
                    ax1.loglog(imls_o, afes, 'silver', linewidth=0.7)
        # if it is, plot in color
        else:
            if m in plot_idx:
                ax[n].loglog(imls, afes, c=viridis(i),
                             label=str(mrs.src_id[ind]))
            if ax1 is not None:
                ax1.loglog(imls_o, afes, c=viridis(i), label=str(mrs.src_id[ind]))
            i += 1


def _plot_m(plt, plot_idx, ax, m, n, imt, AFE, fact, imtls, sid,
            rtgm_probmce, mrs, dstore):
    # identify the sources that have a contribution > than fact (here 10%) of
    # the largest contributor
    fig1, ax1 = plt.subplots()
    # annual frequency of exceedance:
    T = from_string(imt).period
    f = 1 if imt == "PGA" else _find_fact_maxC(T, ASCE_version)

    imls_o = imtls[imt]
    imls = numpy.array([iml * f for iml in imls_o])
    # have to compute everything for max comp. and for geom. mean
    RTGM = rtgm_probmce[m]
    RTGM_o = rtgm_probmce[m] / f

    afe_target = _find_afe_target(imls, AFE[m], RTGM)
    afe_target_o = _find_afe_target(imls_o, AFE[m], RTGM_o)

    # maximum component
    ax[n].loglog(imls, AFE[m], 'k', label=_get_label(imt),
                 linewidth=2, zorder=3)
    ax[n].loglog([numpy.min(imls), RTGM], [afe_target, afe_target], 'k--',
                 linewidth=2, zorder=3)
    ax[n].loglog([RTGM, RTGM], [0, afe_target], 'k--', linewidth=2, zorder=3)
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

    _plot(ax, None, sid, plot_idx, m, n, imls, imls_o,
          mrs, rtgm_probmce, afe_target, fact)

    ax[n].grid('both')
    ax[n].set_xlabel(imt + ' (g)', fontsize=13)
    ax[n].set_ylabel('Annual Freq. Exceedance', fontsize=13)
    ax[n].legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='11')
    ax[n].set_ylim([10E-6, 1.1])
    ax[n].set_xlim([0.01, 5])

    # populate single imt plots - geometric mean
    ax1.grid('both')
    ax1.set_xlabel(imt+' (g)', fontsize=16)
    ax1.set_ylabel('Annual Freq. Exceedance', fontsize=16)
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='13')
    ax1.set_ylim([10E-6, 1.1])
    ax1.set_xlim([0.01, 5])
    # save single imt plot
    bio1 = io.BytesIO()
    fig1.savefig(bio1, format='png', bbox_inches='tight')
    # keep these in webui until we finish checks and have a command
    # line exporter, then we can change the name to _{imt} and they
    # will not appear in the webui
    oq = dstore['oqparam']
    vs30s = oq.override_vs30
    vs30 = vs30s[sid]
    dstore[f'png/disagg_by_src-{imt}-vs30_{vs30}.png'] = Image.open(bio1)
    fig1.tight_layout()


def plot_disagg_by_src(dstore, sid=0, axes=None):
    """
    Plot disaggregation by source

    :param dstore: the datastore
    :param sid: the site ID
    :param axes: list of 3 Axes (for PGA, SA(0.2), SA(1.0)), or None
    :returns: figure of disaggregation by source
    """
    plt = import_plt()
    dinfo = get_info(dstore)
    imtls = dinfo['imtls']
    imts = list(imtls)
    plot_idx = [imts.index('PGA'), imts.index('SA(0.2)'), imts.index('SA(1.0)')]

    rtgm_df = dstore.read_df('rtgm', sel=dict(sid=sid))
    if (rtgm_df.RTGM == 0).all():
        return
    # get hazard curves, put into rates
    AFE = []
    mean_hcurve = dstore['hcurves-stats'][sid, 0]  # shape(M, L1)
    window = dinfo['investigation_time']
    for m, hcurve in enumerate(mean_hcurve):
        AFE.append(to_rates(hcurve, window))
    fact = 0.1
    n = 0

    # if axes not provided, create a figure and axes
    own_fig = False
    if axes is None:
        fig, axes = plt.subplots(3, 1, figsize=(8, 15))
        own_fig = True

    for m, imt in enumerate(imtls):
        if rtgm_df['ProbMCE'][m] == 0:
            continue
        if m in plot_idx:
            _plot_m(plt, plot_idx, axes, m, n, imt, AFE, fact, imtls, sid,
                    rtgm_df['ProbMCE'], dstore['mean_rates_by_src'], dstore)
            n += 1

    if own_fig:
        fig.tight_layout()
        fig.subplots_adjust(hspace=0.3)

    return plt


def plot_sites(dstore, update_dstore=False):
    plt = import_plt()
    sites = dstore['sitecol']
    lons, lats = sites['lon'], sites['lat']
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.grid(True)
    if len(sites) == 1:
        markersize = 30
        marker = 'x'
        padding = 20
    elif len(sites) < 50:
        markersize = 1
        marker = 'o'
        padding = 10
    elif len(sites) < 500:
        markersize = 0.1
        marker = 'o'
        padding = 5
    else:
        markersize = 0.05
        marker = 'o'
        padding = 0
    plt.scatter(lons, lats, c='black', marker=marker, s=markersize)
    xlim, ylim = auto_limits(ax)
    add_borders(ax, readinput.read_countries_df, buffer=0.)
    adjust_limits(ax, xlim, ylim, padding=padding)
    if update_dstore:
        bio = io.BytesIO()
        fig.savefig(bio, format='png', bbox_inches='tight')
        dstore['png/site.png'] = Image.open(bio)
    fig.tight_layout()
    return plt
