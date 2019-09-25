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
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

'''
Module :mod:`openquake.hmtk.seismicity.smoothing.kernels.isotropic_gaussian`
imports :class:`openquake.hmtk.seismicity.smoothing.kernels.isotropic_gaussian.IsotropicGaussian`
the simple isotropic Gaussian smoothing kernel as described by Frankel (1995)

Frankel, A. (1995) Mapping Seismic Hazard in the Central and Eastern United
States. Seismological Research Letters. 66(4) 8 - 21
'''

import numpy as np
from openquake.hmtk.seismicity.utils import haversine
from openquake.hmtk.seismicity.smoothing.kernels.base import (
    BaseSmoothingKernel)


class IsotropicGaussian(BaseSmoothingKernel):
    '''
    Applies a simple isotropic Gaussian smoothing using an Isotropic Gaussian
    Kernel - taken from Frankel (1995) approach
    '''

    def smooth_data(self, data, config, is_3d=False):
        '''
        Applies the smoothing kernel to the data

        :param np.ndarray data:
            Raw earthquake count in the form [Longitude, Latitude, Depth,
                Count]
        :param dict config:
            Configuration parameters must contain:
            * BandWidth: The bandwidth of the kernel (in km) (float)
            * Length_Limit: Maximum number of standard deviations

        :returns:
            * smoothed_value: np.ndarray vector of smoothed values
            * Total (summed) rate of the original values
            * Total (summed) rate of the smoothed values
        '''
        max_dist = config['Length_Limit'] * config['BandWidth']
        smoothed_value = np.zeros(len(data), dtype=float)
        for iloc in range(0, len(data)):
            dist_val = haversine(data[:, 0], data[:, 1],
                                 data[iloc, 0], data[iloc, 1])

            if is_3d:
                dist_val = np.sqrt(dist_val.flatten() ** 2.0 +
                                   (data[:, 2] - data[iloc, 2]) ** 2.0)
            id0 = np.where(dist_val <= max_dist)[0]
            w_val = (np.exp(-(dist_val[id0] ** 2.0) /
                            (config['BandWidth'] ** 2.))).flatten()
            smoothed_value[iloc] = np.sum(w_val * data[id0, 3]) / np.sum(w_val)
        return smoothed_value, np.sum(data[:, -1]), np.sum(smoothed_value)
