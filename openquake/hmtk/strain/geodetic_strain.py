# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2025 GEM Foundation, G. Weatherill, M. Pagani,
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

"""
:class:`openquake.hmtk.strain.geodectic_strain.GeodeticStain` is a
core class for storage and implementation of a geodetic strain rate
model
"""
import numpy as np
from copy import deepcopy

DATA_VARIABLES = ["longitude", "latitude", "exx", "eyy", "exy"]


class GeodeticStrain(object):
    """
    :class:`openquake.hmtk.strain.geodetic_strain.GeodeticStrain` describes
    the geodetic strain model

    :param dict data:
        Strain data in the form of a dictionary where is vector of attributes
        is stored under the correponding dictionary key (i.e.
        - longitude - Longitude of point
        - latitude - Latitiude of point
        - exx - xx-component of strain tensor
        - eyy - yy-component of strain tensor
        - exy - xy-component of strain tensor
    :param numpy.ndarray seismicity_rate:
        Seismicity rate at each point associated with the strain model
    :param numpy.ndarray target_magnitudes:
        Magnitudes for the corresponding activity rates
    :param list data_variables:
        List of strain data attributes in the current class
    """

    def __init__(self):
        """Instantiates"""
        self.data = None
        self.regions = None
        self.seismicity_rate = None
        self.regionalisation = None
        self.target_magnitudes = None
        self.data_variables = []

    def get_secondary_strain_data(self, strain_data=None):
        """
        Calculate the following and add to data dictionary:
        1) 2nd invarient of strain
        2) Dilatation rate
        3) e1h and e2h
        4) err

        :param dict strain_data:
            Strain data dictionary (as described) - will overwrite current
            data if input

        """
        if strain_data:
            self.data = strain_data

        if not isinstance(self.data, dict):
            raise ValueError("Strain data not input or incorrectly formatted")

        # Check to ensure essential attributes are in data dictionary
        for essential_key in DATA_VARIABLES:
            if essential_key not in self.data:
                print(self.data)
                raise ValueError(
                    "Essential strain information %s missing!" % essential_key
                )
        self.data_variables = deepcopy(DATA_VARIABLES)

        # Second Invarient
        self.data["2nd_inv"] = np.sqrt(
            (self.data["exx"] ** 2.0)
            + (self.data["eyy"] ** 2.0)
            + 2.0 * (self.data["exy"] ** 2.0)
        )
        # Dilatation
        self.data["dilatation"] = self.data["exx"] + self.data["eyy"]
        # err
        self.data["err"] = -1.0 * self.data["dilatation"]
        center_normal_rate = (self.data["exx"] + self.data["eyy"]) / 2.0
        radius_rate = np.sqrt(
            (self.data["exx"] - center_normal_rate) ** 2.0
            + (self.data["exy"] ** 2.0)
        )
        # e1h and e2h
        self.data["e1h"] = center_normal_rate - radius_rate
        self.data["e2h"] = center_normal_rate + radius_rate
        self.data["area"] = np.zeros(self.get_number_observations())
        self.data_variables.extend(
            ["2nd_inv", "dilatation", "err", "e1h", "e2h"]
        )

    def get_number_observations(self):
        """
        Returns the number of observations in the data file
        """
        if isinstance(self.data, dict) and ("exx" in self.data.keys()):
            return len(self.data["exx"])
        else:
            return 0
