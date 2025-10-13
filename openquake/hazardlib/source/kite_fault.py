# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.source.kite_fault` defines
:class:`KiteFaultSource`.
"""
import copy
import collections
import numpy as np
from typing import Tuple
from openquake.baselib import general
from openquake.hazardlib import mfd
from openquake.hazardlib.geo import Point, Polygon
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.surface.kite_fault import (
        get_profiles_from_simple_fault_data)
from openquake.hazardlib.source.base import ParametricSeismicSource
from openquake.hazardlib.geo.surface.kite_fault import KiteSurface
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture \
    as ppr


def _get_meshes(omsh, rup_s, rup_d, f_strike, f_dip):
    meshes = []

    # When f_strike is negative, the floating distance is interpreted as
    # a fraction of the rupture length (i.e. a multiple of the sampling
    # distance)
    if f_strike < 0:
        f_strike = int(np.floor(rup_s * abs(f_strike) + 1e-5))
        if f_strike < 1:
            f_strike = 1

    # See f_strike comment above
    if f_dip < 0:
        f_dip = int(np.floor(rup_d * abs(f_dip) + 1e-5))
        if f_dip < 1:
            f_dip = 1

    # Float the rupture on the mesh describing the surface of the fault
    mesh_x_len = omsh.lons.shape[1] - rup_s + 1
    mesh_y_len = omsh.lons.shape[0] - rup_d + 1
    x_nodes = np.arange(0, mesh_x_len, f_strike)
    y_nodes = np.arange(0, mesh_y_len, f_dip)

    while (len(x_nodes) > 0 and f_strike > 1
            and x_nodes[-1] != omsh.lons.shape[1] - rup_s):
        f_strike -= 1
        x_nodes = np.arange(0, mesh_x_len, f_strike)

    while (len(y_nodes) > 0 and f_dip > 1
            and y_nodes[-1] != omsh.lons.shape[0] - rup_d):
        f_dip -= 1
        y_nodes = np.arange(0, mesh_y_len, f_dip)

    for i in x_nodes:
        for j in y_nodes:
            nel = np.size(omsh.lons[j:j + rup_d, i:i + rup_s])
            nna = np.sum(np.isfinite(omsh.lons[j:j + rup_d, i:i + rup_s]))
            prc = nna / nel * 100.

            # Yield only the ruptures that do not contain NaN
            if prc > 99.99 and nna >= 4:
                msh = Mesh(omsh.lons[j:j + rup_d, i:i + rup_s],
                           omsh.lats[j:j + rup_d, i:i + rup_s],
                           omsh.depths[j:j + rup_d, i:i + rup_s])
                meshes.append(msh)
    return meshes


class KiteFaultSource(ParametricSeismicSource):
    """
    Kite fault source
    """
    code = b'K'
    MODIFICATIONS = {'adjust_mfd_from_slip'}

    def __init__(self, source_id, name, tectonic_region_type, mfd,
                 rupture_mesh_spacing, magnitude_scaling_relationship,
                 rupture_aspect_ratio, temporal_occurrence_model,
                 # kite fault specific parameters
                 profiles, rake, floating_x_step=0,
                 floating_y_step=0, profiles_sampling=None):
        super().__init__(
            source_id, name, tectonic_region_type, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio,
            temporal_occurrence_model)

        # TODO add checks
        self.profiles = profiles
        if profiles_sampling is None:
            self.profiles_sampling = rupture_mesh_spacing / rupture_aspect_ratio
        self.rake = rake
        self.floating_x_step = floating_x_step
        self.floating_y_step = floating_y_step

    @classmethod
    def as_simple_fault(cls, param,
                        # simple fault specific parameters
                        upper_seismogenic_depth, lower_seismogenic_depth,
                        fault_trace, dip, rake, floating_x_step,
                        floating_y_step):

        # Get profiles
        profiles = get_profiles_from_simple_fault_data(
            fault_trace, upper_seismogenic_depth, lower_seismogenic_depth,
            dip, param.rupture_mesh_spacing)

        # Creating Kite Source
        self = cls(param.source_id, param.name, param.tectonic_region_type,
                   param.mfd, param.rupture_mesh_spacing,
                   param.magnitude_scaling_relationship,
                   param.rupture_aspect_ratio, param.temporal_occurrence_model,
                   profiles, rake, floating_x_step,
                   floating_y_step)
        return self

    @general.cached_property
    def surface(self) -> KiteSurface:
        """
        :returns:
            The surface of the fault
        """
        # Get the surface of the fault
        # TODO we must automate the definition of the idl parameter
        return KiteSurface.from_profiles(self.profiles,
                                         self.profiles_sampling,
                                         self.rupture_mesh_spacing,
                                         idl=False, align=False)

    def count_ruptures(self) -> int:
        """
        :returns:
            The number of ruptures that this source generates
        """
        if self.num_ruptures:
            return self.num_ruptures
    
        # Counting ruptures and rates
        self._rupture_count = collections.Counter()
        self._rupture_rates = collections.Counter()
        for mag, occ_rate, meshes in self._gen_meshes():
            n = len(meshes)
            mag_str = '{:.2f}'.format(mag)
            self._rupture_count[mag_str] += n
            self._rupture_rates[mag_str] += occ_rate * n
        return sum(self._rupture_count.values())

    def iter_ruptures(self, **kwargs):
        """
        See :meth:
        `openquake.hazardlib.source.base.BaseSeismicSource.iter_ruptures`.
        """
        # Set magnitude scaling relationship, temporal occurrence model and
        # mesh of the fault surface
        step = kwargs.get('step', 1)
        for mag, occ_rate, meshes in self._gen_meshes(step):
            for msh in meshes[::step]:
                surf = KiteSurface(msh)
                hypocenter = surf.get_center()
                # Yield an instance of a ParametricProbabilisticRupture
                yield ppr(mag, self.rake, self.tectonic_region_type,
                          hypocenter, surf, occ_rate,
                          self.temporal_occurrence_model)

    def _gen_meshes(self, step=1):
        surface = self.surface
        for mag, mag_occ_rate in self.get_annual_occurrence_rates()[::step]:

            # Compute the area, length and width of the ruptures
            area = self.magnitude_scaling_relationship.get_median_area(
                mag=mag, rake=self.rake)
            lng, wdt = get_discrete_dimensions(
                area, self.rupture_mesh_spacing,
                self.rupture_aspect_ratio, self.profiles_sampling)

            # Get the number of nodes along the strike and dip. Note that
            # len and wdt should be both multiples of the sampling distances
            # used along the strike and width
            rup_len = int(np.round(lng/self.rupture_mesh_spacing)) + 1
            rup_wid = int(np.round(wdt/self.profiles_sampling)) + 1

            if self.floating_x_step == 0:
                fstrike = 1
            else:
                # ratio = the amount of overlap between consecutive ruptures
                fstrike = int(np.floor(rup_len*self.floating_x_step))
                if fstrike == 0:
                    fstrike = 1

            if self.floating_x_step == 0:
                fdip = 1
            else:
                # as for strike: ratio indicates percentage overlap
                fdip = int(np.floor(rup_wid*self.floating_y_step))
                if fdip == 0:
                    fdip = 1

            # Get the geometry of all the ruptures that the fault surface
            # accommodates
            meshes = _get_meshes(surface.mesh, rup_len, rup_wid, fstrike, fdip)
            if len(meshes):
                yield mag, mag_occ_rate / len(meshes), meshes

    def get_fault_surface_area(self) -> float:
        """
        Returns the area of the fault surface
        """
        raise NotImplementedError

    def __iter__(self):
        """
        This method splits the ruptures by magnitude and yields as many sources
        as the number of magnitude bins admitted by the original source.
        """
        if not hasattr(self, '_rupture_rates'):
            self.count_ruptures()
        if len(self._rupture_rates) == 1:  # not splittable
            yield self
            return
        for mag_str in self._rupture_count:
            if self._rupture_rates[mag_str] == 0:
                continue
            src = copy.copy(self)
            mag = float(mag_str)
            src.mfd = mfd.ArbitraryMFD([mag], [self._rupture_rates[mag_str]])
            src.num_ruptures = self._rupture_count[mag_str]
            yield src

    @property
    def polygon(self):
        """
        The underlying polygon
        `"""
        lons, lats = self.surface.surface_projection
        return Polygon([Point(lo, la) for lo, la in zip(lons, lats)])

    def wkt(self):
        """
        :returns: the geometry as a WKT string
        """
        return self.polygon.wkt


def get_discrete_dimensions(area: float, sampling: float, aspr: float,
                            sampling_y: float = None) -> Tuple[float, float]:
    """
    Computes the discrete dimensions of a rupture given rupture area, sampling
    distance (along strike) and aspect ratio.

    :param area:
        The area of the rupture as obtained from a magnitude scaling
        relationship
    :param sampling:
        The sampling distance [km] along the strike
    :param aspr:
        The rupture aspect ratio [L/W]
    :param sampling_y:
        The sampling distance [km] along the dip
    :returns:
        Lenght [km] and the width [km] of the rupture, respectively
    """

    lenghts = []
    widths = []

    # Set the sampling distance along the dip
    sampling_y = sampling if sampling_y is None else sampling_y

    # Give preference to rectangular ruptures elongated along the strike when
    # the aspect ratio is equal to 1
    if aspr % 1 < 0.01:
        aspr += 0.05

    # Computing possible length and width - length rounded up to a multiple of
    # the sampling distance along strike
    lenghts.append(np.ceil((area * aspr)**0.5/sampling)*sampling)
    widths.append(np.ceil(lenghts[-1]/aspr/sampling_y)*sampling_y)
    widths.append(np.floor(lenghts[-1]/aspr/sampling_y)*sampling_y)

    # Computing possible length and width - length rounded down to a multiple
    # of the sampling distance along strike
    lenghts.append(np.floor((area * aspr)**0.5/sampling)*sampling)
    widths.append(np.ceil(lenghts[-1]/aspr/sampling_y)*sampling_y)
    widths.append(np.floor(lenghts[-1]/aspr/sampling_y)*sampling_y)

    # Select the best combination of length and width taking into account
    # the input values of the rupture area and aspect ratio
    a = np.tile(np.array(lenghts), (1, 4)).flatten()
    b = np.tile(np.array(widths), (1, 2)).flatten()
    areas = a*b
    idx = np.argmin((abs(areas-area))**0.5 + abs(a/b-aspr)*sampling)

    assert isinstance(idx, np.int64)
    lng = a[idx]
    wdt = b[idx]

    # Check the difference between the computed and original value of the
    # rupture area
    area_error = abs(lng*wdt-area)/area

    # Check that the rupture size is compatible with the original value
    # provided. If not, we raise a Value Error
    if (abs(wdt-sampling_y) < 1e-10 or abs(lng-sampling) < 1e-10 and
            area_error > 0.3):
        wdt = None
        lng = None
    elif area_error > 0.25 and lng > 1e-10 and wdt > 1e-10:
        msg = '\nSampling along strike : {:f}\n'.format(sampling)
        msg += 'Sampling along dip   : {:f}\n'.format(sampling_y)
        msg += 'Area expected        : {:f}\n'.format(area)
        msg += 'Area computed        : {:f}\n'.format(lng*wdt)
        raise ValueError(msg)
    return lng, wdt
