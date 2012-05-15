# Copyright (c) 2010-2012, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.


"""Simple objects models to represent elements of NRML artifacts. These models
are intended to be produced by NRML XML parsers and consumed by NRML XML
serializers.
"""


class SiteModel(object):
    """Basic object representation of a single node in a model of site-specific
    parameters.

    :param float vs30:
        Average shear wave velocity for top 30 m. Units m/s.
    :param str vs30_type:
        'measured' or 'inferred'. Identifies if vs30 value has been measured or
        inferred.
    :param float z1pt0:
        Depth to shear wave velocity of 1.0 km/s. Units m.
    :param float z2pt5:
        Depth to shear wave velocity of 2.5 km/s. Units km.
    :param wkt:
        Well-known text (POINT) represeting the location of these parameters.
    """

    def __init__(self, vs30=None, vs30_type=None, z1pt0=None, z2pt5=None,
                 wkt=None):
        self.vs30 = vs30
        self.vs30_type = vs30_type
        self.z1pt0 = z1pt0
        self.z2pt5 = z2pt5
        self.wkt = wkt
