#!/usr/bin/env/python

'''
Module :mod: 'hmtk.plotting.seismicity.completeness.plot_stepp_1971' 
creates plot to illustrate outcome of Stepp (1972) method for completeness 
analysis
'''
import os.path
import numpy as np
import matplotlib.pyplot as plt

valid_markers = ['*', '+', '1', '2', '3', '4', '8', '<', '>', 'D', 'H', '^',
                 '_', 'd', 'h', 'o', 'p', 's', 'v', 'x', '|']


def create_stepp_plot(model, filename, filetype='png', 
    filedpi=300):
    '''
    Creates the classic Stepp (1972) plots for a completed Stepp analysis, 
    and exports the figure to a file.
    :param model:
        Completed Stepp (1972) analysis as instance of :class:
        'hmtk.seismicity.completeness.comp_stepp_1971.Stepp1971'
    :param string filename: 
        Name of output file
    :param string filetype: 
        Type of file (from list supported by matplotlib)
    :param int filedpi:
        Resolution (dots per inch) of output file
    '''
    if os.path.exists(filename):
        raise IOError('File already exists!')
    
    legend_list = [(str(model.magnitude_bin[iloc] + 0.01) + ' - ' + 
                   str(model.magnitude_bin[iloc + 1])) for iloc in range(0, 
                   len(model.magnitude_bin) - 1)]
    
    rgb_list = []
    marker_vals = []
    # Get marker from valid list
    while len(valid_markers) < len(model.magnitude_bin):
        valid_markers.append(valid_markers)
    
    marker_sampler = np.arange(0, len(valid_markers),1)
    np.random.shuffle(marker_sampler)
    # Get colour for each bin
    for value in range(0, len(model.magnitude_bin) - 1):
        rgb_samp = np.random.uniform(0., 1., 3)
        rgb_list.append((rgb_samp[0], rgb_samp[1], rgb_samp[2]))
        marker_vals.append(valid_markers[marker_sampler[value]])
    # Plot observed Sigma lambda
    for iloc in range(0, len(model.magnitude_bin) - 1):
        plt.loglog(model.time_values, 
                   model.sigma[:, iloc],
                   linestyle='None',
                   marker=marker_vals[iloc], 
                   color=rgb_list[iloc])
    
    plt.legend(legend_list)
    # Plot expected Poisson rate
    for iloc in range(0, len(model.magnitude_bin) - 1):
        plt.loglog(model.time_values, 
                   model.model_line[:,iloc], 
                   linestyle='-',
                   marker='None',
                   color=rgb_list[iloc])
        xmarker = model.end_year - model.completeness_table[iloc, 0]
        id0 = model.model_line[:, iloc] > 0.
        ymarker = 10.0 ** np.interp(np.log10(xmarker),
                                    np.log10(model.time_values[id0]),
                                    np.log10(model.model_line[id0, iloc]))
        plt.loglog(xmarker, ymarker, 'ks')
    plt.xlabel('Time (years)', fontsize=15)
    plt.ylabel('$\sigma_{\lambda} = \sqrt{\lambda} / \sqrt{T}$', 
                fontsize=15)
    # Save figure to file
    plt.savefig(filename, dpi=filedpi, format=filetype)
