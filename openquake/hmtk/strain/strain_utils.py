# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2019 GEM Foundation, G. Weatherill, M. Pagani,
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
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
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

'''
Module :mod:`openquake.hmtk.strain.utils` holds a set of useful
utility functions for the strain rate model calculations
'''

import numpy as np
from math import exp


def moment_function(magnitude):
    '''
    Get moment (in Nm) from magnitude using Hanks & Kanamori (1979)

    :param float (or numpy.ndarray) magnitude:
        Magnitude of event
    :returns:
        Seismic Moment in Nm
    '''
    return 10. ** ((1.5 * magnitude) + 9.05)


def moment_magnitude_function(moment):
    '''
    For a given moment, get the moment magnitude using the formula
    of Hanks & Kanamori (1979)

    :param float or numpy.ndarray magnitude
        Seismic moment in Nm
    '''

    return (2. / 3.) * (np.log10(moment) - 9.05)


def calculate_taper_function(obs_threshold_moment, sel_threshold_moment,
                             corner_moment, beta):
    '''
    Calculates the tapering function of the tapered Gutenberg & Richter model:
    as described in Bird & Liu (2007)::

     taper_function = (M_0(M_T) / M_0(M_T^{CMT}))^-beta x exp((M_0(m_T^CMT) -
         M_0(m_T)) / M_0(m_c))

    :param numpy.ndarray obs_threshold_moment:
        Moment of the threshold magnitude of the observed earthquake catalogue
    :param numpy.ndarray sel_threshold_moment:
        Moment of the target magnitude
    :param float corner_momnet:
        Corner moment of the Tapered Gutenberg-Richter Function
    :param float beta:
        Beta value (b * ln(10.)) of the Tapered Gutenberg-Richter Function
    :returns:
        Relative moment rate
    '''
    argument = (obs_threshold_moment - sel_threshold_moment) /\
        corner_moment
    if argument < -100.0:
        g_function = 0.0
    else:
        g_function = ((sel_threshold_moment / obs_threshold_moment) **
                      -beta) * exp(argument)
    return g_function


def tapered_gutenberg_richter_cdf(moment, moment_threshold, beta,
                                  corner_moment):
    '''
    Tapered Gutenberg Richter Cumulative Density Function

    :param float or numpy.ndarray moment:
        Moment for calculation of rate

    :param float or numpy.ndarray moment_threshold:
        Threshold Moment of the distribution (moment rate essentially!)

    :param float beta:
        Beta value (b * ln(10.)) of the Tapered Gutenberg-Richter Function

    :param float corner_momnet:
        Corner moment of the Tapered Gutenberg-Richter Function

    :returns:
        Cumulative probability of moment release > moment


    '''
    cdf = np.exp((moment_threshold - moment) / corner_moment)
    return ((moment / moment_threshold) ** (-beta)) * cdf


def tapered_gutenberg_richter_pdf(moment, moment_threshold, beta,
                                  corner_moment):
    '''
    Tapered Gutenberg-Richter Probability Density Function

    :param float or numpy.ndarray moment:
        Moment for calculation of rate

    :param float or numpy.ndarray moment_threshold:
        Threshold Moment of the distribution (moment rate essentially!)

    :param float beta:
        Beta value (b * ln(10.)) of the Tapered Gutenberg-Richter Function

    :param float corner_momnet:
        Corner moment of the Tapered Gutenberg-Richter Function

    :returns:
        Absolute probability of moment release > moment
    '''
    return ((beta / moment + 1. / corner_moment) *
            tapered_gutenberg_richter_cdf(moment, moment_threshold, beta,
                                          corner_moment))
