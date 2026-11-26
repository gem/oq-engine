# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
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

A kite fault source describes a fault whose geometry is given by a set of
profiles, i.e. polylines sampling the fault surface along the dip direction.
The profiles are resampled and joined into a
:class:`openquake.hazardlib.geo.surface.kite_fault.KiteSurface`, a
(possibly irregular) mesh of nodes with rows running along strike and
columns running along dip. For each magnitude of the magnitude-frequency
distribution, ruptures are obtained by floating a rectangle of nodes, whose
size is derived from the magnitude scaling relationship and the rupture
aspect ratio, over this mesh.
"""
import copy
import collections
import numpy as np
from typing import Tuple
from openquake.baselib import general
from openquake.hazardlib import mfd
from openquake.hazardlib.codes import KITE_FAULT
from openquake.hazardlib.geo import Point, Polygon
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.surface.kite_fault import (
        get_profiles_from_simple_fault_data)
from openquake.hazardlib.source.base import ParametricSeismicSource
from openquake.hazardlib.geo.surface.kite_fault import KiteSurface
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture \
    as ppr


def _get_meshes(omsh, rup_s, rup_d, f_strike, f_dip):
    """
    Floats a rupture of `rup_s` x `rup_d` nodes over the mesh of the fault
    surface and returns the meshes of all the admissible ruptures.

    The steps used to move the rupture along strike and dip are reduced
    (down to 1) until the last rupture in each direction touches the end of
    the fault mesh, so that the whole surface is covered. Ruptures
    containing nodes with NaN coordinates (i.e. falling partially outside
    an irregular fault surface) are discarded.

    :param omsh:
        A :class:`openquake.hazardlib.geo.mesh.Mesh` instance describing the
        surface of the fault. Rows are along dip, columns along strike.
    :param rup_s:
        The number of nodes of the rupture along the strike
    :param rup_d:
        The number of nodes of the rupture along the dip
    :param f_strike:
        The floating step along the strike. When positive, it is a number of
        nodes; when negative, its absolute value is a fraction of the rupture
        length (i.e. of `rup_s`)
    :param f_dip:
        The floating step along the dip. Same convention as `f_strike`, with
        the fraction referred to the rupture width (i.e. to `rup_d`)
    :returns:
        A list of :class:`openquake.hazardlib.geo.mesh.Mesh` instances, one
        for each rupture
    """
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
    Kite fault source.

    A fault source whose geometry is defined by a set of profiles (see the
    module docstring). Ruptures are generated by floating, for each
    magnitude of the MFD, a rectangular patch of nodes over the mesh of the
    fault surface; the occurrence rate of each magnitude is distributed
    evenly among the ruptures with that magnitude.

    Parameters from ``source_id`` to ``temporal_occurrence_model`` are
    documented in :class:`openquake.hazardlib.source.base.BaseSeismicSource`
    and :class:`openquake.hazardlib.source.base.ParametricSeismicSource`.
    Note that ``rupture_mesh_spacing`` is the sampling distance [km] used
    along the strike of the fault.

    :param profiles:
        A list of :class:`openquake.hazardlib.geo.line.Line` instances, each
        one describing a profile of the fault surface along the dip. The
        profiles are ordered along strike
    :param rake:
        The rake angle [degrees] of the ruptures
    :param floating_x_step:
        The floating step along strike, as a fraction of the rupture length.
        For example 0.5 means that consecutive ruptures overlap by half of
        their length. The default, 0, means that the rupture floats at every
        node of the mesh
    :param floating_y_step:
        The floating step along dip, as a fraction of the rupture width.
        Same convention as `floating_x_step`
    :param profiles_sampling:
        The sampling distance [km] used along the profiles (i.e. along dip).
        When not given it is computed as
        ``rupture_mesh_spacing / rupture_aspect_ratio``
    """
    code = KITE_FAULT
    MODIFICATIONS = {
        'adjust_aspect_ratio',
        'adjust_mfd_from_slip',
        'set_aspect_ratio',
        'set_msr',
    }

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
        else:
            self.profiles_sampling = profiles_sampling
        self.rake = rake
        self.floating_x_step = floating_x_step
        self.floating_y_step = floating_y_step


    @classmethod
    def from_simple_fault(cls, src, floating_x_step=0, floating_y_step=0,
                          profiles_sampling=None):
        """
        Builds a kite fault source from a
        :class:`openquake.hazardlib.source.SimpleFaultSource`. The profiles
        of the kite fault are derived from the trace, dip and seismogenic
        depths of the simple fault, see :meth:`as_simple_fault`.

        :param src:
            A :class:`openquake.hazardlib.source.SimpleFaultSource` instance
        :param floating_x_step:
            The floating step along strike, as a fraction of the rupture
            length (0 means floating at every node)
        :param floating_y_step:
            The floating step along dip, as a fraction of the rupture width
            (0 means floating at every node)
        :param profiles_sampling:
            The sampling distance [km] along the profiles. When `None` it is
            computed from the mesh spacing and the aspect ratio
        :returns:
            A :class:`KiteFaultSource` instance
        """
        return cls.as_simple_fault(
                src.source_id,
                src.name,
                src.tectonic_region_type,
                src.mfd,
                src.rupture_mesh_spacing,
                src.magnitude_scaling_relationship,
                src.rupture_aspect_ratio,
                src.temporal_occurrence_model,
                upper_seismogenic_depth=src.upper_seismogenic_depth,
                lower_seismogenic_depth=src.lower_seismogenic_depth,
                fault_trace=src.fault_trace,
                dip=src.dip,
                rake=src.rake,
                floating_x_step=floating_x_step,
                floating_y_step=floating_y_step,
                profiles_sampling=profiles_sampling)

    # The signature of as_simple_fault is intentionally kept explicit
    @classmethod
    def as_simple_fault(cls, source_id, name, tectonic_region_type,
                        mfd, rupture_mesh_spacing,
                        magnitude_scaling_relationship, rupture_aspect_ratio,
                        temporal_occurrence_model,
                        *,
                        # simple fault specific parameters
                        upper_seismogenic_depth, lower_seismogenic_depth,
                        fault_trace, dip, rake, floating_x_step=0,
                        floating_y_step=0, profiles_sampling=None):
        """
        Builds a kite fault source using the parameters describing a simple
        fault. The profiles are straight lines, spaced
        `rupture_mesh_spacing` along the fault trace, that dip with angle
        `dip` from the upper to the lower seismogenic depth (see
        :func:`openquake.hazardlib.geo.surface.kite_fault.get_profiles_from_simple_fault_data`).

        Parameters from ``source_id`` to ``temporal_occurrence_model`` are
        the same as for :class:`KiteFaultSource`.

        :param upper_seismogenic_depth:
            The upper seismogenic depth [km]
        :param lower_seismogenic_depth:
            The lower seismogenic depth [km]
        :param fault_trace:
            A :class:`openquake.hazardlib.geo.line.Line` instance with the
            trace of the fault
        :param dip:
            The dip angle [degrees] of the fault
        :param rake:
            The rake angle [degrees] of the ruptures
        :param floating_x_step:
            See :class:`KiteFaultSource`
        :param floating_y_step:
            See :class:`KiteFaultSource`
        :param profiles_sampling:
            See :class:`KiteFaultSource`
        :returns:
            A :class:`KiteFaultSource` instance
        """
        # Get profiles
        profiles = get_profiles_from_simple_fault_data(
            fault_trace, upper_seismogenic_depth, lower_seismogenic_depth,
            dip, rupture_mesh_spacing)

        # Creating Kite Source
        return cls(source_id, name, tectonic_region_type, mfd,
                   rupture_mesh_spacing, magnitude_scaling_relationship,
                   rupture_aspect_ratio, temporal_occurrence_model,
                   profiles, rake, floating_x_step, floating_y_step,
                   profiles_sampling)

    @general.cached_property
    def surface(self) -> KiteSurface:
        """
        :returns:
            The :class:`KiteSurface` of the fault, built from the profiles
            resampled at `profiles_sampling` along dip and at
            `rupture_mesh_spacing` along strike. Computed once and cached
        """
        # Get the surface of the fault
        # TODO we must automate the definition of the idl parameter
        return KiteSurface.from_profiles(self.profiles,
                                         self.profiles_sampling,
                                         self.rupture_mesh_spacing,
                                         idl=False, align=False)

    def count_ruptures(self) -> int:
        """
        Counts the ruptures generated by the source. As a side effect, it
        stores in `_rupture_count` and `_rupture_rates` the number of
        ruptures and the total occurrence rate per magnitude (keyed by the
        magnitude formatted with two decimals); these are used by
        :meth:`__iter__` to split the source.

        :returns:
            The number of ruptures that this source generates
        """
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

        Supported keyword arguments:

        - ``step``: subsampling factor; one rupture every ``step ** 2`` is
          kept for each magnitude (default 1, i.e. all the ruptures)
        - ``rates``: if true, instead of ruptures yield, for each magnitude,
          an array with the occurrence rates of the (sampled) ruptures

        :yields:
            :class:`openquake.hazardlib.source.rupture.ParametricProbabilisticRupture`
            instances whose hypocenter is the centre of the rupture surface,
            or arrays of rates if ``rates`` is set
        """
        # Set magnitude scaling relationship, temporal occurrence model and
        # mesh of the fault surface
        step = kwargs.get('step', 1)
        only_rates = kwargs.get('rates')
        for mag, occ_rate, meshes in self._gen_meshes():
            # the meshes cover a 2D grid of positions (along strike and
            # dip), so the subsampling is quadratic in the step, as for
            # the simple faults; this matters in preclassical, see
            # ContextMaker.estimate_weight
            sampled = meshes[::step ** 2]
            if only_rates:
                yield np.full(len(sampled), occ_rate)
                continue
            for msh in sampled:
                surf = KiteSurface(msh)
                hypocenter = surf.get_center()
                # Yield an instance of a ParametricProbabilisticRupture
                yield ppr(mag, self.rake, self.tectonic_region_type,
                          hypocenter, surf, occ_rate,
                          self.temporal_occurrence_model)

    def _gen_meshes(self):
        """
        For each magnitude of the MFD, computes the rupture dimensions from
        the magnitude scaling relationship and the aspect ratio, converts
        them into a number of nodes and floats the rupture over the fault
        mesh. Magnitudes whose ruptures are too small to be represented with
        the sampling distances, or for which no rupture fits the surface,
        are skipped.

        :yields:
            Triples (magnitude, occurrence rate of each rupture, list of
            rupture meshes). The rate of each rupture is the annual rate of
            the magnitude divided by the number of ruptures
        """
        surface = self.surface
        for mag, mag_occ_rate in self.get_annual_occurrence_rates():

            # Compute the area, length and width of the ruptures
            area = self.magnitude_scaling_relationship.get_median_area(
                mag=mag, rake=self.rake)
            lng, wdt = get_discrete_dimensions(
                area, self.rupture_mesh_spacing,
                self.rupture_aspect_ratio, self.profiles_sampling)

            # The rupture is too small to be represented with the sampling
            # distances adopted: skip this magnitude
            if lng is None or wdt is None:
                continue

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

            if self.floating_y_step == 0:
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
        Returns the area of the fault surface. Not implemented for kite
        faults.

        :raises NotImplementedError:
        """
        raise NotImplementedError

    def __iter__(self):
        """
        This method splits the ruptures by magnitude and yields as many sources
        as the number of magnitude bins admitted by the original source.
        Each source is a shallow copy of the original one with an
        :class:`openquake.hazardlib.mfd.ArbitraryMFD` containing a single
        magnitude, whose rate is the total rate of the ruptures with that
        magnitude. Magnitudes with zero rate are skipped. If the source
        has a single magnitude it yields itself.
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
            src._num_ruptures = self._rupture_count[mag_str]
            yield src

    @property
    def polygon(self):
        """
        :returns:
            A :class:`openquake.hazardlib.geo.Polygon` with the surface
            projection of the fault
        """
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

    The length is rounded up and down to a multiple of `sampling` and, for
    each length, the width is rounded up and down to a multiple of
    `sampling_y`. Among these candidates, the pair that best matches the
    target area and aspect ratio is selected. When the aspect ratio is an
    integer, it is slightly increased to favour ruptures elongated along
    strike.

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
        Length [km] and the width [km] of the rupture, respectively. Both
        are `None` when the rupture is too small to be represented with
        the given sampling distances
    :raises ValueError:
        When the area of the discretized rupture differs from `area` by
        more than 25%
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
