# The Hazard Library
# Copyright (C) 2012-2018 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.hazardlib.mgmpe` provides additional
functionalities to the class :class:`ground shaking intensity models <GMPE>`
"""

import re
from openquake.hazardlib.gsim.base import GMPE


class MGMPE(GMPE):
    """
    Implements a meta GMPE class that can be used to instantiate new GMPEs
    starting from existing ones.

    :param gmpes:
        Can be either a single :class:`~openquake.hazardlib.gsim.base.GMPE`
        instance or a list of instances of the same class.
    """

    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = None
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set(())
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set(())
    DEFINED_FOR_TECTONIC_REGION_TYPE = None
    REQUIRES_DISTANCES = set(())
    REQUIRES_RUPTURE_PARAMETERS = set(())
    REQUIRES_SITES_PARAMETERS = set(())

    def __init__(self, gmpes):
        if len(gmpes) < 2:
            gmpes = [gmpes]
        self.gmpes = gmpes
        self._set_parameters()

    def _set_parameters(self):
        """
        Get the parameters assigned to the original GMPEs and merge them into
        a new set to be used with the meta GMPE. Currently we do not perform
        consistency tests but this is something that it will be added soon.
        """
        keys = {}
        for key in dir(self):
            if re.search('^[A-Z]', key) and not re.search('^C', key):
                keys[key] = set(())
        for gmpe in self.gmpes:
            for key in dir(gmpe):
                if re.search('^[A-Z]', key) and not re.search('^C', key):
                    tmps = getattr(gmpe, key)
                    try:
                        keys[key] |= tmps
                    except TypeError:
                        print('This is not a recognized type')
                    else:
                        keys[key] = tmps
        for key in keys:
            setattr(self, key, keys[key])
            print(key, getattr(self, key))
