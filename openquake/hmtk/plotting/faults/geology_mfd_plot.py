#!/usr/bin/env python
"""

"""

import numpy as np
import matplotlib.pyplot as plt
from openquake.hmtk.faults.fault_models import RecurrenceBranch
from openquake.hmtk.plotting.seismicity.catalogue_plots import _save_image


#
# def _get_occurence_array(mmin, bin_width, occurrence):
#    """
#    Returns the incremental and cumulative recurrence
#    """
#    mags = mmin + np.cumsum(bin_width * np.ones(len(occurrence))) - bin_width
#    cumulative = np.array([np.sum(occurrence[iloc:])
#                           for iloc in range(0, len(occurrence))])
#    return np.column_stack([mags, occurrence, cumulative])
#

def plot_recurrence_models(
        configs, area, slip, msr, rake,
        shear_modulus=30.0, disp_length_ratio=1.25E-5, msr_sigma=0.,
        figure_size=(8, 6), filename=None, filetype='png', dpi=300, ax=None):
    """
    Plots a set of recurrence models

    :param list configs:
        List of configuration dictionaries
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figure_size)
    else:
        fig = ax.get_figure()

    for config in configs:
        model = RecurrenceBranch(area, slip, msr, rake, shear_modulus,
                                 disp_length_ratio, msr_sigma, weight=1.0)
        model.get_recurrence(config)
        occurrence = model.recurrence.occur_rates
        cumulative = np.array([np.sum(occurrence[iloc:])
                               for iloc in range(0, len(occurrence))])
        if 'AndersonLuco' in config['Model_Name']:
            flt_label = config['Model_Name'] + ' - ' + config['Model_Type'] +\
                ' Type'
        else:
            flt_label = config['Model_Name']
        flt_color = np.random.uniform(0.1, 1.0, 3)
        ax.semilogy(model.magnitudes, cumulative, '-', label=flt_label,
                    color=flt_color, linewidth=2.)
        ax.semilogy(model.magnitudes, model.recurrence.occur_rates, '--',
                    color=flt_color, linewidth=2.)

    ax.set_xlabel('Magnitude')
    ax.set_ylabel('Annual Rate')
    ax.legend(bbox_to_anchor=(1.1, 1.0))
    _save_image(fig, filename, filetype, dpi)
