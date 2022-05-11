# The Hazard Library
# Copyright (C) 2012-2022 GEM Foundation
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
Module :mod:`openquake.hazardlib.source.base` defines a base class for
seismic sources.
"""
import abc
import math
import zlib
import numpy
from openquake.baselib import general
from openquake.baselib.performance import compile, numba
from openquake.hazardlib import mfd
from openquake.hazardlib.geo import Point, geodetic
from openquake.hazardlib.geo.surface.planar import (
    PlanarSurface, build_planar_array)
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture

F8 = numba.float64
surfin_dt = numpy.dtype([
    ('usd', float),
    ('lsd', float),
    ('rar', float),
    ('mag', float),
    ('area', float),
    ('strike', float),
    ('dip', float),
    ('rake', float),
    ('lon', float),
    ('lat', float),
    ('dep', float),
    ('dims', (float, 3)),
])


@compile("(f8[:, :], f8, f8, f8, f8[:], f8, f8, f8, f8, f8, f8)")
def _update(corners, usd, lsd, mag, dims, strike, dip, rake, clon, clat, cdep):
    # from the rupture center we can now compute the coordinates of the
    # four coorners by moving along the diagonals of the plane. This seems
    # to be better then moving along the perimeter, because in this case
    # errors are accumulated that induce distorsions in the shape with
    # consequent raise of exceptions when creating PlanarSurface objects
    # theta is the angle between the diagonal of the surface projection
    # and the line passing through the rupture center and parallel to the
    # top and bottom edges. Theta is zero for vertical ruptures (because
    # rup_proj_width is zero)
    half_length, half_width, half_height = dims / 2.
    rdip = math.radians(dip)

    # precalculated azimuth values for horizontal-only and vertical-only
    # moves from one point to another on the plane defined by strike
    # and dip:
    azimuth_right = strike
    azimuth_down = azimuth_right + 90
    azimuth_left = azimuth_down + 90
    azimuth_up = azimuth_left + 90

    # half height of the vertical component of rupture width
    # is the vertical distance between the rupture geometrical
    # center and it's upper and lower borders:
    # calculate how much shallower the upper border of the rupture
    # is than the upper seismogenic depth:
    vshift = usd - cdep + half_height
    # if it is shallower (vshift > 0) than we need to move the rupture
    # by that value vertically.
    if vshift < 0:
        # the top edge is below upper seismogenic depth. now we need
        # to check that we do not cross the lower border.
        vshift = lsd - cdep - half_height
        if vshift > 0:
            # the bottom edge of the rupture is above the lower seismo
            # depth; that means that we don't need to move the rupture
            # as it fits inside seismogenic layer.
            vshift = 0
        # if vshift < 0 than we need to move the rupture up.

    # now we need to find the position of rupture's geometrical center.
    # in any case the hypocenter point must lie on the surface, however
    # the rupture center might be off (below or above) along the dip.
    if vshift != 0:
        # we need to move the rupture center to make the rupture fit
        # inside the seismogenic layer.
        hshift = abs(vshift / math.tan(rdip))
        clon, clat = geodetic.fast_point_at(
            clon, clat, azimuth_up if vshift < 0 else azimuth_down,
            hshift)
        cdep += vshift
    theta = math.degrees(math.atan(half_width / half_length))
    hor_dist = math.sqrt(half_length ** 2 + half_width ** 2)
    corners[0, :2] = geodetic.fast_point_at(
        clon, clat, strike + 180 + theta, hor_dist)
    corners[1, :2] = geodetic.fast_point_at(
        clon, clat, strike - theta, hor_dist)
    corners[2, :2] = geodetic.fast_point_at(
        clon, clat, strike + 180 - theta, hor_dist)
    corners[3, :2] = geodetic.fast_point_at(
        clon, clat, strike + theta, hor_dist)
    corners[0:2, 2] = cdep - half_height
    corners[2:4, 2] = cdep + half_height
    corners[4, 0] = strike
    corners[4, 1] = dip
    corners[4, 2] = rake
    corners[5, 0] = clon
    corners[5, 1] = clat
    corners[5, 2] = cdep


# numbified below, ultrafast
def build_corners(usd, lsd, mag, dims, strike, dip, rake, lon, lat, deps):
    (M, N), D = usd.shape, len(deps)
    corners = numpy.zeros((6, M, N, D, 3))
    # 0,1,2,3: tl, tr, bl, br
    # 4: (strike, dip, rake)
    # 5: hypo
    for m in range(M):
        for n in range(N):
            for d, dep in enumerate(deps):
                _update(corners[:, m, n, d], usd[m, n], lsd[m, n], mag[m, n],
                        dims[m, n], strike[m, n], dip[m, n], rake[m, n],
                        lon, lat, dep)
    return corners


if numba:
    build_corners = compile(F8[:, :, :, :, :](
        F8[:, :],     # usd
        F8[:, :],     # lsd
        F8[:, :],     # mag
        F8[:, :, :],  # dims
        F8[:, :],     # strike
        F8[:, :],     # dip
        F8[:, :],     # rake
        F8,           # lon
        F8,           # lat
        F8[:],        # dep
    ))(build_corners)


def build_planar_surfaces(surfin, lon, lat, deps, shift_hypo=False):
    """
    :param surfin:
        Surface input parameters as an array of shape (M, N)
    :param lon, lat
        Longitude and latitude of the hypocenters (scalars)
    :parameter deps:
        Depths of the hypocenters (vector)
    :param shift_hypo:
        If true, change .hc to the shifted hypocenter
    :return:
        an array of PlanarSurfaces of shape (M, N, D)
    """
    corners = build_corners(
        surfin.usd, surfin.lsd, surfin.mag, surfin.dims,
        surfin.strike, surfin.dip, surfin.rake, lon, lat, numpy.array(deps))
    planar_array = build_planar_array(corners[:4], corners[4], corners[5])
    out = numpy.zeros(surfin.shape + (len(deps),), object)  # shape (M, N, D)
    M, N, D = out.shape
    for m in range(M):
        for n in range(N):
            for d in range(D):
                surface = PlanarSurface.from_(planar_array[m, n, d])
                if shift_hypo:
                    surface.hc = Point(*corners[5, m, n, d])
                else:
                    surface.hc = Point(lon, lat, deps[d])
                out[m, n, d] = surface
    return out


def get_code2cls():
    """
    :returns: a dictionary source code -> source class
    """
    dic = {}
    for cls in general.gen_subclasses(BaseSeismicSource):
        if hasattr(cls, 'code'):
            dic[cls.code] = cls
    return dic


class BaseSeismicSource(metaclass=abc.ABCMeta):
    """
    Base class representing a seismic source, that is a structure generating
    earthquake ruptures.

    :param source_id:
        Some (numeric or literal) source identifier. Supposed to be unique
        within the source model.
    :param name:
        String, a human-readable name of the source.
    :param tectonic_region_type:
        Source's tectonic regime. See :class:`openquake.hazardlib.const.TRT`.
    """
    id = -1  # to be set
    trt_smr = 0  # set by the engine
    nsites = 1  # set when filtering the source
    min_mag = 0  # set in get_oqparams and CompositeSourceModel.filter
    splittable = True
    checksum = 0  # set in source_reader
    weight = 1  # set in contexts

    @abc.abstractproperty
    def MODIFICATIONS(self):
        pass

    @property
    def trt_smrs(self):
        """
        :returns: a list of integers (usually of 1 element)
        """
        trt_smr = self.trt_smr
        return [trt_smr] if isinstance(trt_smr, int) else trt_smr

    def serial(self, ses_seed):
        """
        :returns: a random seed derived from source_id and ses_seed
        """
        return zlib.crc32(self.source_id.encode('ascii'), ses_seed)

    def __init__(self, source_id, name, tectonic_region_type):
        self.source_id = source_id
        self.name = name
        self.tectonic_region_type = tectonic_region_type
        self.trt_smr = -1  # set by the engine
        self.num_ruptures = 0  # set by the engine
        self.seed = None  # set by the engine
        self.min_mag = 0  # set by the SourceConverter

    def is_gridded(self):
        """
        :returns: True if the source contains only gridded ruptures
        """
        return False

    @abc.abstractmethod
    def iter_ruptures(self, **kwargs):
        """
        Get a generator object that yields probabilistic ruptures the source
        consists of.

        :returns:
            Generator of instances of sublclass of :class:
            `~openquake.hazardlib.source.rupture.BaseProbabilisticRupture`.
        """

    def sample_ruptures(self, eff_num_ses, ses_seed):
        """
        :param eff_num_ses: number of stochastic event sets * number of samples
        :yields: triples (rupture, trt_smr, num_occurrences)
        """
        seed = self.serial(ses_seed)
        numpy.random.seed(seed)
        for trt_smr in self.trt_smrs:
            for rup, num_occ in self._sample_ruptures(eff_num_ses):
                rup.rup_id = seed
                if hasattr(rup, 'occurrence_rate'):
                    # defined only for poissonian sources
                    rup.occurrence_rate *= self.smweight
                seed += 1
                yield rup, trt_smr, num_occ

    def _sample_ruptures(self, eff_num_ses):
        tom = getattr(self, 'temporal_occurrence_model', None)
        if tom:  # time-independent source
            yield from self.sample_ruptures_poissonian(eff_num_ses)
        else:  # time-dependent source (nonparametric)
            mutex_weight = getattr(self, 'mutex_weight', 1)
            for rup in self.iter_ruptures():
                occurs = rup.sample_number_of_occurrences(eff_num_ses)
                if mutex_weight < 1:
                    # consider only the occurrencies below the mutex_weight
                    occurs *= (numpy.random.random(eff_num_ses) < mutex_weight)
                num_occ = occurs.sum()
                if num_occ:
                    yield rup, num_occ

    def get_mags(self):
        """
        :returns: the magnitudes of the ruptures contained in the source
        """
        mags = set()
        if hasattr(self, 'get_annual_occurrence_rates'):
            for mag, rate in self.get_annual_occurrence_rates():
                mags.add(mag)
        elif hasattr(self, 'source_file'):
            # unbound UCERFSource
            mags.add(numpy.nan)
        elif hasattr(self, 'mags'):  # MultiFaultSource
            mags.update(mag for mag in self.mags if mag >= self.min_mag)
        else:  # nonparametric
            for rup, pmf in self.data:
                if rup.mag >= self.min_mag:
                    mags.add(rup.mag)
        return sorted(mags)

    def sample_ruptures_poissonian(self, eff_num_ses):
        """
        :param eff_num_ses: number of stochastic event sets * number of samples
        :yields: pairs (rupture, num_occurrences[num_samples])
        """
        tom = self.temporal_occurrence_model
        if not hasattr(self, 'nodal_plane_distribution'):  # fault
            ruptures = list(self.iter_ruptures())
            rates = numpy.array([rup.occurrence_rate for rup in ruptures])
            occurs = numpy.random.poisson(rates * tom.time_span * eff_num_ses)
            for rup, num_occ in zip(ruptures, occurs):
                if num_occ:
                    yield rup, num_occ
            return
        # else (multi)point sources and area sources
        rup_args = []
        rates = []
        for src in self:
            lon, lat = src.location.x, src.location.y
            for mag, mag_occ_rate in src.get_annual_occurrence_rates():
                if mag < self.min_mag:
                    continue
                for np_prob, np in src.nodal_plane_distribution.data:
                    for hc_prob, hc_depth in src.hypocenter_distribution.data:
                        args = (mag_occ_rate, np_prob, hc_prob,
                                mag, np, lon, lat, hc_depth, src)
                        rup_args.append(args)
                        rates.append(mag_occ_rate * np_prob * hc_prob)
        eff_rates = numpy.array(rates) * tom.time_span * eff_num_ses
        occurs = numpy.random.poisson(eff_rates)
        for num_occ, args, rate in zip(occurs, rup_args, rates):
            if num_occ:
                _, np_prob, hc_prob, mag, np, lon, lat, hc_depth, src = args
                hc = Point(lon, lat, hc_depth)
                [[[surface]]] = build_planar_surfaces(
                    src.get_surfin([mag], [np]), lon, lat, [hc.depth])
                rup = ParametricProbabilisticRupture(
                    mag, np.rake, src.tectonic_region_type, hc,
                    surface, rate, tom)
                yield rup, num_occ

    @abc.abstractmethod
    def get_one_rupture(self, ses_seed, rupture_mutex=False):
        """
        Yields one random rupture from a source
        """

    def __iter__(self):
        """
        Override to implement source splitting
        """
        yield self

    @abc.abstractmethod
    def count_ruptures(self):
        """
        Return the number of ruptures that will be generated by the source.
        """

    @abc.abstractmethod
    def get_min_max_mag(self):
        """
        Return minimum and maximum magnitudes of the ruptures generated
        by the source.
        """

    def modify(self, modification, parameters):
        """
        Apply a single modificaton to the source parameters
        Reflects the modification method and calls it passing ``parameters``
        as keyword arguments.

        Modifications can be applied one on top of another. The logic
        of stacking modifications is up to a specific source implementation.

        :param modification:
            String name representing the type of modification.
        :param parameters:
            Dictionary of parameters needed for modification.
        :raises ValueError:
            If ``modification`` is missing from the attribute `MODIFICATIONS`.
        """
        if modification not in self.MODIFICATIONS:
            raise ValueError('Modification %s is not supported by %s' %
                             (modification, type(self).__name__))
        meth = getattr(self, 'modify_%s' % modification)
        meth(**parameters)

    def to_xml(self):
        """
        Convert the source into an XML string, very useful for debugging
        """
        from openquake.hazardlib import nrml, sourcewriter
        return nrml.to_string(sourcewriter.obj_to_node(self))

    def __repr__(self):
        """
        String representation of a source, displaying the source class name
        and the source id.
        """
        return '<%s %s, weight=%.1f>' % (
            self.__class__.__name__, self.source_id, self.weight)


class ParametricSeismicSource(BaseSeismicSource, metaclass=abc.ABCMeta):
    """
    Parametric Seismic Source generates earthquake ruptures from source
    parameters, and associated probabilities of occurrence are defined through
    a magnitude frequency distribution and a temporal occurrence model.

    :param mfd:
        Magnitude-Frequency distribution for the source.
        See :mod:`openquake.hazardlib.mfd`.
    :param rupture_mesh_spacing:
        The desired distance between two adjacent points in source's
        ruptures' mesh, in km. Mainly this parameter allows to balance
        the trade-off between time needed to compute the :meth:`distance
        <openquake.hazardlib.geo.surface.base.BaseSurface.get_min_distance>`
        between the rupture surface and a site and the precision of that
        computation.
    :param magnitude_scaling_relationship:
        Instance of subclass of
        :class:`openquake.hazardlib.scalerel.base.BaseMSR` to
        describe how does the area of the rupture depend on magnitude and rake.
    :param rupture_aspect_ratio:
        Float number representing how much source's ruptures are more wide
        than tall. Aspect ratio of 1 means ruptures have square shape,
        value below 1 means ruptures stretch vertically more than horizontally
        and vice versa.
    :param temporal_occurrence_model:
        Instance of
        :class:`openquake.hazardlib.tom.PoissonTOM` defining temporal
        occurrence model for calculating rupture occurrence probabilities

    :raises ValueError:
        If either rupture aspect ratio or rupture mesh spacing is not positive
        (if not None).
    """

    def __init__(self, source_id, name, tectonic_region_type, mfd,
                 rupture_mesh_spacing, magnitude_scaling_relationship,
                 rupture_aspect_ratio, temporal_occurrence_model):
        super().__init__(source_id, name, tectonic_region_type)

        if rupture_mesh_spacing is not None and not rupture_mesh_spacing > 0:
            raise ValueError('rupture mesh spacing must be positive')

        if rupture_aspect_ratio is not None and not rupture_aspect_ratio > 0:
            raise ValueError('rupture aspect ratio must be positive')

        self.mfd = mfd
        self.rupture_mesh_spacing = rupture_mesh_spacing
        self.magnitude_scaling_relationship = magnitude_scaling_relationship
        self.rupture_aspect_ratio = rupture_aspect_ratio
        self.temporal_occurrence_model = temporal_occurrence_model

    def get_annual_occurrence_rates(self, min_rate=0):
        """
        Get a list of pairs "magnitude -- annual occurrence rate".

        The list is taken from assigned MFD object
        (see :meth:`openquake.hazardlib.mfd.base.BaseMFD.get_annual_occurrence_rates`)
        with simple filtering by rate applied.

        :param min_rate:
            A non-negative value to filter magnitudes by minimum annual
            occurrence rate. Only magnitudes with rates greater than that
            are included in the result list.
        :returns:
            A list of two-item tuples -- magnitudes and occurrence rates.
        """
        scaling_rate = getattr(self, 'scaling_rate', 1)
        return [(mag, occ_rate * scaling_rate)
                for (mag, occ_rate) in self.mfd.get_annual_occurrence_rates()
                if (min_rate is None or occ_rate > min_rate) and
                mag >= self.min_mag]

    def get_min_max_mag(self):
        """
        Get the minimum and maximum magnitudes of the ruptures generated
        by the source from the underlying MFD.
        """
        min_mag, max_mag = self.mfd.get_min_max_mag()
        return max(self.min_mag, min_mag), max_mag

    def get_one_rupture(self, ses_seed, rupture_mutex=False):
        """
        Yields one random rupture from a source. IMPORTANT: this method
        does not take into account the frequency of occurrence of the
        ruptures
        """
        # The Mutex case is admitted only for non-parametric ruptures
        msg = 'Mutually exclusive ruptures are admitted only in case of'
        msg += ' non-parametric sources'
        assert (not rupture_mutex), msg
        # Set random seed and get the number of ruptures
        num_ruptures = self.count_ruptures()
        seed = self.serial(ses_seed)
        numpy.random.seed(seed)
        idx = numpy.random.choice(num_ruptures)
        # NOTE Would be nice to have a method generating a rupture given two
        # indexes, one for magnitude and one setting the position
        for i, rup in enumerate(self.iter_ruptures()):
            if i == idx:
                if hasattr(self, 'rup_id'):
                    rup.rup_id = self.rup_id
                rup.idx = idx
                return rup

    def modify_set_msr(self, new_msr):
        """
        Updates the MSR originally assigned to the source

        :param new_msr:
            An instance of the :class:`openquake.hazardlib.scalerel.BaseMSR`
        """
        self.magnitude_scaling_relationship = new_msr

    def modify_set_slip_rate(self, slip_rate: float):
        """
        Updates the slip rate assigned to the source

        :param slip_rate:
            The value of slip rate [mm/yr]
        """
        self.slip_rate = slip_rate

    def modify_set_mmax_truncatedGR(self, mmax: float):
        """
        Updates the mmax assigned. This works on for parametric MFDs.s

        :param mmax:
            The value of the new maximum magnitude
        """
        # Check that the current src has a TruncatedGRMFD MFD
        msg = 'This modification works only when the source MFD is a '
        msg += 'TruncatedGRMFD'
        assert self.mfd.__class__.__name__ == 'TruncatedGRMFD', msg
        self.mfd.max_mag

    def modify_recompute_mmax(self, epsilon: float = 0):
        """
        Updates the value of mmax using the msr and the area of the fault

        :param epsilon:
            Number of standard deviations to be added or substracted
        """
        msr = self.magnitude_scaling_relationship
        area = self.get_fault_surface_area()  # area in km^2
        mag = msr.get_median_mag(area=area, rake=self.rake)
        std = msr.get_std_dev_mag(area=area, rake=self.rake)
        self.mfd.max_mag = mag + epsilon * std

    def modify_adjust_mfd_from_slip(self, slip_rate: float, rigidity: float,
                                    recompute_mmax: float = None):
        """
        :slip_rate:
            A float defining slip rate [in mm]
        :rigidity:
            A float defining material rigidity [in GPa]
        :rigidity:
            A float defining material rigidity [in GPa]
        """
        # Check that the current src has a TruncatedGRMFD MFD
        msg = 'This modification works only when the source MFD is a '
        msg += 'TruncatedGRMFD'
        assert self.mfd.__class__.__name__ == 'TruncatedGRMFD', msg
        # Compute moment
        area = self.get_fault_surface_area() * 1e6  # area in m^2
        rigidity *= 1e9  # rigidity in Pa
        slip_rate *= 1e-3  # slip rate in m
        mo = rigidity * area * slip_rate
        # Update the MFD
        min_mag = self.mfd.min_mag
        max_mag = self.mfd.max_mag
        bin_w = self.mfd.bin_width
        b_val = self.mfd.b_val
        self.mfd = mfd.TruncatedGRMFD.from_moment(min_mag, max_mag, bin_w,
                                                  b_val, mo)
