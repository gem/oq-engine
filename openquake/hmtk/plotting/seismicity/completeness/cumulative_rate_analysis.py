# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
# 
# The software is NOT distributed as part of GEM's OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

#!/usr/bin/env python

'''
Module openquake.hmtk.plotting.seismicity.completeness.simple_completeness is a graphical
function for estimating the completeness period of magnitude intervals
by plotting the cumulative rate of events with time in each interval
'''

import numpy as np
import pylab
import matplotlib.pyplot as plt
from openquake.hmtk.seismicity.completeness.base import (
    BaseCatalogueCompleteness)


class SimpleCumulativeRate(BaseCatalogueCompleteness):
    '''
    Class to define the temporal variation in completess using simple
    changes in cumulative rates in individual completeness bins
    '''
    def completeness(self, catalogue, config, saveplot=False, filetype='png',
                     timeout=120):
        '''
        :param catalogue:
            Earthquake catalogue as instance of
            :class:`openquake.hmtk.seismicity.catalogue.Catalogue`
        :param dict config:
            Configuration parameters of the algorithm, containing the
            following information:
            'magnitude_bin' Size of magnitude bin (non-negative float)
            'time_bin' Size (in dec. years) of the time window (non-negative
            float)
            'increment_lock' Boolean to indicate whether to ensure
            completeness magnitudes always decrease with more
            recent bins
        :returns:
            2-column table indicating year of completeness and corresponding
            magnitude numpy.ndarray
        '''
        if saveplot and not isinstance(saveplot, str):
            raise ValueError('To save the figures enter a filename: ')

        # Get magntitude bins
        magnitude_bins = self._get_magnitudes_from_spacing(
            catalogue.data['magnitude'],
            config['magnitude_bin'])
        dec_time = catalogue.get_decimal_time()
        completeness_table = np.zeros([len(magnitude_bins) - 1, 2],
                                      dtype=float)
        min_year = float(np.min(catalogue.data['year']))
        max_year = float(np.max(catalogue.data['year'])) + 1.0
        has_completeness = np.zeros(len(magnitude_bins) - 1, dtype=bool)
        for iloc in range(0, len(magnitude_bins) - 1):
            lower_mag = magnitude_bins[iloc]
            upper_mag = magnitude_bins[iloc + 1]
            idx = np.logical_and(catalogue.data['magnitude'] >= lower_mag,
                                 catalogue.data['magnitude'] < upper_mag)
            cumvals = np.cumsum(np.ones(np.sum(idx)))
            plt.plot(dec_time[idx], cumvals, '.')
            plt.xlim(min_year, max_year + 5)
            title_string = 'Magnitude %5.2f to %5.2f' % (lower_mag, upper_mag)
            plt.title(title_string)
            pts = pylab.ginput(1, timeout=timeout)[0]
            if pts[0] <= max_year:
                 # Magnitude bin has no completeness!
                has_completeness[iloc] = True
            completeness_table[iloc, 0] = np.floor(pts[0])
            completeness_table[iloc, 1] = magnitude_bins[iloc]
            print(completeness_table[iloc, :], has_completeness[iloc])
            if config['increment_lock'] and (iloc > 0) and \
                (completeness_table[iloc, 0] > completeness_table[iloc - 1, 0]):
                    completeness_table[iloc, 0] = \
                        completeness_table[iloc - 1, 0]
            # Add marker line to indicate completeness point
            marker_line = np.array([
                    [0., completeness_table[iloc, 0]],
                    [cumvals[-1], completeness_table[iloc, 0]]])
            plt.plot(marker_line[:, 0], marker_line[:, 1], 'r-')
            if saveplot:
                filename = saveplot + '_' + ('%5.2f' % lower_mag) + (
                    '%5.2f' % upper_mag) + '.' + filetype
                plt.savefig(filename, format=filetype)
            plt.close()
        return completeness_table[has_completeness, :]

    def _get_magnitudes_from_spacing(self, magnitudes, delta_m):
        '''If a single magnitude spacing is input then create the bins

        :param numpy.ndarray magnitudes:
            Vector of earthquake magnitudes

        :param float delta_m:
            Magnitude bin width

        :returns: Vector of magnitude bin edges (numpy.ndarray)
        '''
        min_mag = np.min(magnitudes)
        max_mag = np.max(magnitudes)
        if (max_mag - min_mag) < delta_m:
            raise ValueError('Bin width greater than magnitude range!')
        mag_bins = np.arange(np.floor(min_mag), np.ceil(max_mag), delta_m)
        # Check to see if there are magnitudes in lower and upper bins
        is_mag = np.logical_and(mag_bins - max_mag < delta_m,
                                min_mag - mag_bins < delta_m)
        mag_bins = mag_bins[is_mag]
        return mag_bins
