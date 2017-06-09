# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import copy
import time
import math
import os.path
import logging
import collections
import h5py
import numpy

from openquake.baselib.general import AccumDict
from openquake.baselib.python3compat import zip
from openquake.baselib import parallel
from openquake.hazardlib import nrml
from openquake.risklib import riskinput
from openquake.commonlib import readinput, source, calc, util
from openquake.calculators import base, event_based
from openquake.calculators.event_based_risk import (
    EbriskCalculator, event_based_risk)

from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.geodetic import min_idx_dst, min_geodetic_distance
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.hazardlib.source.characteristic import CharacteristicFaultSource
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.calc.filters import SourceFilter, FarAwayRupture
from openquake.hazardlib.mfd import EvenlyDiscretizedMFD
from openquake.hazardlib.sourceconverter import SourceConverter

# ######################## rupture calculator ############################ #

U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32

# DEFAULT VALUES FOR UCERF BACKGROUND MODELS
DEFAULT_MESH_SPACING = 1.0
DEFAULT_TRT = "Active Shallow Crust"
HDD = PMF([(0.2, 3.0), (0.6, 6.0), (0.2, 9.0)])
NPD = PMF([(0.15, NodalPlane(0.0, 90.0, 0.0)),
           (0.15, NodalPlane(45.0, 90.0, 0.0)),
           (0.15, NodalPlane(90.0, 90.0, 0.0)),
           (0.15, NodalPlane(135.0, 90.0, 0.0)),
           (0.05, NodalPlane(0.0, 45.0, 90.)),
           (0.05, NodalPlane(45.0, 45.0, 90.)),
           (0.05, NodalPlane(90.0, 45.0, 90.)),
           (0.05, NodalPlane(135.0, 45.0, 90.)),
           (0.05, NodalPlane(180.0, 45.0, 90.)),
           (0.05, NodalPlane(225.0, 45.0, 90.)),
           (0.05, NodalPlane(270.0, 45.0, 90.)),
           (0.05, NodalPlane(325.0, 45.0, 90.))])


class ImperfectPlanarSurface(PlanarSurface):
    """
    The planar surface class sets a narrow tolerance for the rectangular plane
    to be distorted in cartesian space. Ruptures with aspect ratios << 1.0,
    and with a dip of less than 90 degrees, cannot be generated in a manner
    that is consistent with the definitions - and thus cannot be instantiated.
    This subclass modifies the original planar surface class such that the
    tolerance checks are over-ridden. We find that distance errors with respect
    to a simple fault surface with a mesh spacing of 0.001 km are only on the
    order of < 0.15 % for Rrup (< 2 % for Rjb, < 3.0E-5 % for Rx)
    """
    IMPERFECT_RECTANGLE_TOLERANCE = numpy.inf


def get_rupture_dimensions(mag, nodal_plane, msr, rupture_aspect_ratio,
                           upper_seismogenic_depth, lower_seismogenic_depth):
    """
    Calculate and return the rupture length and width
    for given magnitude ``mag`` and nodal plane.

    :param nodal_plane:
        Instance of :class:`openquake.hazardlib.geo.nodalplane.NodalPlane`.
    :returns:
        Tuple of two items: rupture length in width in km.

    The rupture area is calculated using method
    :meth:`~openquake.hazardlib.scalerel.base.BaseMSR.get_median_area`
    of source's
    magnitude-scaling relationship. In any case the returned
    dimensions multiplication is equal to that value. Than
    the area is decomposed to length and width with respect
    to source's rupture aspect ratio.

    If calculated rupture width being inclined by nodal plane's
    dip angle would not fit in between upper and lower seismogenic
    depth, the rupture width is shrunken to a maximum possible
    and rupture length is extended to preserve the same area.
    """
    area = msr.get_median_area(mag, nodal_plane.rake)
    rup_length = math.sqrt(area * rupture_aspect_ratio)
    rup_width = area / rup_length
    seismogenic_layer_width = (lower_seismogenic_depth -
                               upper_seismogenic_depth)
    max_width = (seismogenic_layer_width /
                 math.sin(math.radians(nodal_plane.dip)))
    if rup_width > max_width:
        rup_width = max_width
        rup_length = area / rup_width
    return rup_length, rup_width


def get_rupture_surface(mag, nodal_plane, hypocenter, msr,
                        rupture_aspect_ratio, upper_seismogenic_depth,
                        lower_seismogenic_depth, mesh_spacing=1.0):
    """
    Create and return rupture surface object with given properties.

    :param mag:
        Magnitude value, used to calculate rupture dimensions,
        see :meth:`_get_rupture_dimensions`.
    :param nodal_plane:
        Instance of :class:`openquake.hazardlib.geo.nodalplane.NodalPlane`
        describing the rupture orientation.
    :param hypocenter:
        Point representing rupture's hypocenter.
    :returns:
        Instance of
        :class:`~openquake.hazardlib.geo.surface.planar.PlanarSurface`.
    """
    assert (upper_seismogenic_depth <= hypocenter.depth
            and lower_seismogenic_depth >= hypocenter.depth)
    rdip = math.radians(nodal_plane.dip)

    # precalculated azimuth values for horizontal-only and vertical-only
    # moves from one point to another on the plane defined by strike
    # and dip:
    azimuth_right = nodal_plane.strike
    azimuth_down = (azimuth_right + 90) % 360
    azimuth_left = (azimuth_down + 90) % 360
    azimuth_up = (azimuth_left + 90) % 360

    rup_length, rup_width = get_rupture_dimensions(
        mag, nodal_plane, msr, rupture_aspect_ratio, upper_seismogenic_depth,
        lower_seismogenic_depth)
    # calculate the height of the rupture being projected
    # on the vertical plane:
    rup_proj_height = rup_width * math.sin(rdip)
    # and it's width being projected on the horizontal one:
    rup_proj_width = rup_width * math.cos(rdip)

    # half height of the vertical component of rupture width
    # is the vertical distance between the rupture geometrical
    # center and it's upper and lower borders:
    hheight = rup_proj_height / 2
    # calculate how much shallower the upper border of the rupture
    # is than the upper seismogenic depth:
    vshift = upper_seismogenic_depth - hypocenter.depth + hheight
    # if it is shallower (vshift > 0) than we need to move the rupture
    # by that value vertically.
    if vshift < 0:
        # the top edge is below upper seismogenic depth. now we need
        # to check that we do not cross the lower border.
        vshift = lower_seismogenic_depth - hypocenter.depth - hheight
        if vshift > 0:
            # the bottom edge of the rupture is above the lower sesmogenic
            # depth. that means that we don't need to move the rupture
            # as it fits inside seismogenic layer.
            vshift = 0
        # if vshift < 0 than we need to move the rupture up by that value.

    # now we need to find the position of rupture's geometrical center.
    # in any case the hypocenter point must lie on the surface, however
    # the rupture center might be off (below or above) along the dip.
    rupture_center = hypocenter
    if vshift != 0:
        # we need to move the rupture center to make the rupture fit
        # inside the seismogenic layer.
        hshift = abs(vshift / math.tan(rdip))
        rupture_center = rupture_center.point_at(
            horizontal_distance=hshift, vertical_increment=vshift,
            azimuth=(azimuth_up if vshift < 0 else azimuth_down)
        )

    # from the rupture center we can now compute the coordinates of the
    # four coorners by moving along the diagonals of the plane. This seems
    # to be better then moving along the perimeter, because in this case
    # errors are accumulated that induce distorsions in the shape with
    # consequent raise of exceptions when creating PlanarSurface objects
    # theta is the angle between the diagonal of the surface projection
    # and the line passing through the rupture center and parallel to the
    # top and bottom edges. Theta is zero for vertical ruptures (because
    # rup_proj_width is zero)
    theta = math.degrees(
        math.atan((rup_proj_width / 2.) / (rup_length / 2.))
    )
    hor_dist = math.sqrt(
        (rup_length / 2.) ** 2 + (rup_proj_width / 2.) ** 2
    )
    left_top = rupture_center.point_at(
        horizontal_distance=hor_dist,
        vertical_increment=-rup_proj_height / 2,
        azimuth=(nodal_plane.strike + 180 + theta) % 360
    )
    right_top = rupture_center.point_at(
        horizontal_distance=hor_dist,
        vertical_increment=-rup_proj_height / 2,
        azimuth=(nodal_plane.strike - theta) % 360
    )
    left_bottom = rupture_center.point_at(
        horizontal_distance=hor_dist,
        vertical_increment=rup_proj_height / 2,
        azimuth=(nodal_plane.strike + 180 - theta) % 360
    )
    right_bottom = rupture_center.point_at(
        horizontal_distance=hor_dist,
        vertical_increment=rup_proj_height / 2,
        azimuth=(nodal_plane.strike + theta) % 360
    )
    return PlanarSurface(mesh_spacing, nodal_plane.strike, nodal_plane.dip,
                         left_top, right_top, right_bottom, left_bottom)


def generate_background_ruptures(tom, locations, occurrence, mag, npd,
                                 hdd, upper_seismogenic_depth,
                                 lower_seismogenic_depth, msr=WC1994(),
                                 aspect=1.5, trt=DEFAULT_TRT):
    """
    :param tom:
        Temporal occurrence model as instance of :class:
        openquake.hazardlib.tom.TOM
    :param numpy.ndarray locations:
        Array of locations [Longitude, Latitude] of the point sources
    :param numpy.ndarray occurrence:
        Annual rates of occurrence
    :param float mag:
        Magnitude
    :param npd:
        Nodal plane distribution as instance of :class:
        openquake.hazardlib.pmf.PMF
    :param hdd:
        Hypocentral depth distribution as instance of :class:
        openquake.hazardlib.pmf.PMF
    :param float upper_seismogenic_depth:
        Upper seismogenic depth (km)
    :param float lower_seismogenic_depth:
        Lower seismogenic depth (km)
    :param msr:
        Magnitude scaling relation
    :param float aspect:
        Aspect ratio
    :param str trt:
        Tectonic region type
    :returns:
        List of ruptures
    """
    ruptures = []
    n_vals = len(locations)
    depths = hdd.sample_pairs(n_vals)
    nodal_planes = npd.sample_pairs(n_vals)
    for i, (x, y) in enumerate(locations):
        hypocentre = Point(x, y, depths[i][1])
        surface = get_rupture_surface(mag, nodal_planes[i][1],
                                      hypocentre, msr, aspect,
                                      upper_seismogenic_depth,
                                      lower_seismogenic_depth)
        rupture_probability = (occurrence[i] * nodal_planes[i][0] *
                               depths[i][0])
        ruptures.append(ParametricProbabilisticRupture(
            mag, nodal_planes[i][1].rake, trt, hypocentre, surface,
            PointSource, rupture_probability, tom))
    return ruptures


def sample_background_model(
        hdf5, branch_key, tom, seed, filter_idx, min_mag, npd, hdd,
        upper_seismogenic_depth, lower_seismogenic_depth, msr=WC1994(),
        aspect=1.5, trt=DEFAULT_TRT):
    """
    Generates a rupture set from a sample of the background model

    :param branch_key:
        Key to indicate the branch for selecting the background model
    :param tom:
        Temporal occurrence model as instance of :class:
        openquake.hazardlib.tom.TOM
    :param seed:
        Random seed to use in the call to tom.sample_number_of_occurrences
    :param filter_idx:
        Sites for consideration (can be None!)
    :param float min_mag:
        Minimim magnitude for consideration of background sources
    :param npd:
        Nodal plane distribution as instance of :class:
        openquake.hazardlib.pmf.PMF
    :param hdd:
        Hypocentral depth distribution as instance of :class:
        openquake.hazardlib.pmf.PMF
    :param float aspect:
        Aspect ratio
    :param float upper_seismogenic_depth:
        Upper seismogenic depth (km)
    :param float lower_seismogenic_depth:
        Lower seismogenic depth (km)
    :param msr:
        Magnitude scaling relation
    :param float integration_distance:
        Maximum distance from rupture to site for consideration
    """
    bg_magnitudes = hdf5["/".join(["Grid", branch_key, "Magnitude"])].value
    # Select magnitudes above the minimum magnitudes
    mag_idx = bg_magnitudes >= min_mag
    mags = bg_magnitudes[mag_idx]
    rates = hdf5["/".join(["Grid", branch_key, "RateArray"])][filter_idx, :]
    rates = rates[:, mag_idx]
    valid_locs = hdf5["Grid/Locations"][filter_idx, :]
    # Sample remaining rates
    sampler = tom.sample_number_of_occurrences(rates, seed)
    background_ruptures = []
    background_n_occ = []
    for i, mag in enumerate(mags):
        rate_idx = numpy.where(sampler[:, i])[0]
        rate_cnt = sampler[rate_idx, i]
        occurrence = rates[rate_idx, i]
        locations = valid_locs[rate_idx, :]
        ruptures = generate_background_ruptures(
            tom, locations, occurrence,
            mag, npd, hdd, upper_seismogenic_depth,
            lower_seismogenic_depth, msr, aspect, trt)
        background_ruptures.extend(ruptures)
        background_n_occ.extend(rate_cnt.tolist())
    return background_ruptures, background_n_occ


class UCERFControl(object):
    """
    :param source_file:
        Path to an existing HDF5 file containing the UCERF model
    :param str id:
        Valid branch of UCERF
    :param float investigation_time:
        Investigation time of event set (years)
    :param start_date:
        Starting date of the investigation (None for time independent)
    :param float min_mag:
        Minimim magnitude for consideration of background sources
    :param npd:
        Nodal plane distribution as instance of :class:
        openquake.hazardlib.pmf.PMF
    :param hdd:
        Hypocentral depth distribution as instance of :class:
        openquake.hazardlib.pmf.PMF
    :param float aspect:
        Aspect ratio
    :param float upper_seismoge nic_depth:
        Upper seismogenic depth (km)
    :param float lower_seismogenic_depth:
        Lower seismogenic depth (km)
    :param msr:
        Magnitude scaling relation
    :param float mesh_spacing:
        Spacing (km) of fault mesh
    :param str trt:
        Tectonic region type
    :param float integration_distance:
        Maximum distance from rupture to site for consideration
    """
    def __init__(
            self, source_file, id, investigation_time, start_date, min_mag,
            npd=NPD, hdd=HDD, aspect=1.5, upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=15.0, msr=WC1994(), mesh_spacing=1.0,
            trt="Active Shallow Crust", integration_distance=1000):
        assert os.path.exists(source_file), source_file
        self.source_file = source_file
        self.source_id = id
        self.inv_time = investigation_time
        self.start_date = start_date
        self.tom = self._get_tom()
        self.min_mag = min_mag
        self.npd = npd
        self.hdd = hdd
        self.aspect = aspect
        self.usd = upper_seismogenic_depth
        self.lsd = lower_seismogenic_depth
        self.msr = msr
        self.mesh_spacing = mesh_spacing
        self.tectonic_region_type = trt

    def get_min_max_mag(self):
        """
        Called when updating the SourceGroup
        """
        return self.min_mag, None

    def _get_tom(self):
        """
        Returns the temporal occurence model as a Poisson TOM
        """
        return PoissonTOM(self.inv_time)


class UcerfSource(object):
    """
    Source-like class for use in UCERF calculations. It is build on top
    of an UCERFControl object which wraps the input file in HDF5 format.
    Each source has attributes `.source_id` (the name of the branch),
    `.src_group_id` (the number of the group i.e. of the source model),
    `.num_ruptures` (the number of ruptures in that branch) and `.idx_set`,
    a dictionary of HDF5 keys determined by the `branch_id` string.

    :param control: a :class:`UCERFControl` instance
    :param grp_id: ordinal of the source group
    :param branch_name: name of the UCERF branch
    :param branch_id: string associated to the branch
    """
    tectonic_region_type = DEFAULT_TRT

    def __init__(self, control, grp_id, branch_name, branch_id):
        self.control = control
        self.src_group_id = grp_id
        self.source_id = branch_id
        self.idx_set = build_idx_set(branch_id, control.start_date)
        with h5py.File(self.control.source_file, "r") as hdf5:
            self.num_ruptures = len(hdf5[self.idx_set["rate_idx"]])

    @property
    def weight(self):
        """
        Weight of the source, equal to the number of ruptures contained
        """
        return self.num_ruptures

    def get_rupture_sites(self, hdf5, ridx, src_filter, mag):
        """
        Determines if a rupture is likely to be inside the integration distance
        by considering the set of fault plane centroids and returns the
        affected sites if any.

        :param hdf5:
            Source of UCERF file as h5py.File object
        :param ridx:
            List of indices composing the rupture sections
        :param src_filter:
            SourceFilter instance
        :param mag:
            Magnitude of the rupture for consideration
        :returns:
            The sites affected by the rupture (or None)
        """
        centroids = []
        for idx in ridx:
            trace_idx = "{:s}/{:s}".format(self.idx_set["sec_idx"], str(idx))
            centroids.append(hdf5[trace_idx + "/Centroids"].value)
        centroids = numpy.concatenate(centroids)
        lons, lats = src_filter.sitecol.lons, src_filter.sitecol.lats
        distance = min_geodetic_distance(
            centroids[:, 0], centroids[:, 1], lons, lats)
        idist = src_filter.integration_distance(DEFAULT_TRT, mag)
        return src_filter.sitecol.filter(distance <= idist)

    def get_background_sids(self, src_filter):
        """
        We can apply the filtering of the background sites as a pre-processing
        step - this is done here rather than in the sampling of the ruptures
        themselves
        """
        ctl = self.control
        branch_key = self.idx_set["grid_key"]
        idist = src_filter.integration_distance(DEFAULT_TRT)
        lons, lats = src_filter.sitecol.lons, src_filter.sitecol.lats
        with h5py.File(ctl.source_file, 'r') as hdf5:
            bg_locations = hdf5["Grid/Locations"].value
            n_locations = bg_locations.shape[0]
            distances = min_idx_dst(lons, lats, numpy.zeros_like(lons),
                                    bg_locations[:, 0], bg_locations[:, 1],
                                    numpy.zeros(n_locations))[1]
            # Add buffer equal to half of length of median area from Mmax
            mmax_areas = ctl.msr.get_median_area(
                hdf5["/".join(["Grid", branch_key, "MMax"])].value, 0.0)
            # for instance hdf5['Grid/FM0_0_MEANFS_MEANMSR/MMax']
            mmax_lengths = numpy.sqrt(mmax_areas / ctl.aspect)
            ok = distances <= (0.5 * mmax_lengths + idist)
            # get list of indices from array of booleans
            return numpy.where(ok)[0].tolist()

    def get_ucerf_rupture(self, hdf5, iloc, src_filter):
        """
        :param hdf5:
            Source Model hdf5 object as instance of :class: h5py.File
        :param int iloc:
            Location of the rupture plane in the hdf5 file
        :param src_filter:
            Sites for consideration and maximum distance
        """
        ctl = self.control
        mesh_spacing = ctl.mesh_spacing
        trt = ctl.tectonic_region_type
        ridx = hdf5[self.idx_set["geol_idx"] + "/RuptureIndex"][iloc]
        mag = hdf5[self.idx_set["mag_idx"]][iloc]
        surface_set = []
        r_sites = self.get_rupture_sites(hdf5, ridx, src_filter, mag)
        if r_sites is None:
            return None, None
        for idx in ridx:
            # Build simple fault surface
            trace_idx = "{:s}/{:s}".format(self.idx_set["sec_idx"], str(idx))
            rup_plane = hdf5[trace_idx + "/RupturePlanes"][:].astype("float64")
            for jloc in range(0, rup_plane.shape[2]):
                top_left = Point(rup_plane[0, 0, jloc],
                                 rup_plane[0, 1, jloc],
                                 rup_plane[0, 2, jloc])
                top_right = Point(rup_plane[1, 0, jloc],
                                  rup_plane[1, 1, jloc],
                                  rup_plane[1, 2, jloc])
                bottom_right = Point(rup_plane[2, 0, jloc],
                                     rup_plane[2, 1, jloc],
                                     rup_plane[2, 2, jloc])
                bottom_left = Point(rup_plane[3, 0, jloc],
                                    rup_plane[3, 1, jloc],
                                    rup_plane[3, 2, jloc])
                try:
                    surface_set.append(
                        ImperfectPlanarSurface.from_corner_points(
                            mesh_spacing, top_left, top_right,
                            bottom_right, bottom_left))
                except ValueError as evl:
                    raise ValueError(evl, trace_idx, top_left, top_right,
                                     bottom_right, bottom_left)

        rupture = ParametricProbabilisticRupture(
            mag,
            hdf5[self.idx_set["rake_idx"]][iloc],
            trt,
            surface_set[len(surface_set) // 2].get_middle_point(),
            MultiSurface(surface_set),
            CharacteristicFaultSource,
            hdf5[self.idx_set["rate_idx"]][iloc],
            ctl.tom)

        # Get rupture index code string
        ridx_string = "-".join(str(val) for val in ridx)
        return rupture, ridx_string

    def generate_event_set(self, background_sids, src_filter, seed):
        """
        Generates the event set corresponding to a particular branch
        """
        # get rates from file
        ctl = self.control
        with h5py.File(ctl.source_file, 'r') as hdf5:
            rates = hdf5[self.idx_set["rate_idx"]].value
            occurrences = ctl.tom.sample_number_of_occurrences(rates, seed)
            indices = numpy.where(occurrences)[0]
            logging.debug(
                'Considering "%s", %d ruptures', self.source_id, len(indices))

            # get ruptures from the indices
            ruptures = []
            rupture_occ = []
            for idx, n_occ in zip(indices, occurrences[indices]):
                ucerf_rup, _ = self.get_ucerf_rupture(hdf5, idx, src_filter)
                if ucerf_rup:
                    ruptures.append(ucerf_rup)
                    rupture_occ.append(n_occ)

            # sample background sources
            background_ruptures, background_n_occ = sample_background_model(
                hdf5, self.idx_set["grid_key"], ctl.tom, seed, background_sids,
                ctl.min_mag, ctl.npd, ctl.hdd, ctl.usd, ctl.lsd, ctl.msr,
                ctl.aspect, ctl.tectonic_region_type)
            ruptures.extend(background_ruptures)
            rupture_occ.extend(background_n_occ)
        return ruptures, rupture_occ

    def iter_ruptures(self):
        """
        Yield ruptures for the current set of indices (.rupset_idx)
        """
        ctl = self.control
        with h5py.File(ctl.source_file, "r") as hdf5:
            try:  # the source has set a subset of indices
                rupset_idx = self.rupset_idx
            except AttributeError:  # use all indices
                rupset_idx = numpy.arange(self.num_ruptures)
            rate = hdf5[self.idx_set["rate_idx"]]
            for ridx in rupset_idx:
                # Get the ucerf rupture rate from the MeanRates array
                if not rate[ridx]:
                    # ruptures may have have zero rate
                    continue
                rup, ridx_string = self.get_ucerf_rupture(
                    hdf5, ridx, self.src_filter)
                if rup:
                    yield rup

    def get_background_sources(self, src_filter):
        """
        Turn the background model of a given branch into a set of point sources

        :param src_filter:
            SourceFilter instance
        """
        ctl = self.control
        background_sids = self.get_background_sids(src_filter)
        with h5py.File(ctl.source_file, "r") as hdf5:
            grid_loc = "/".join(["Grid", self.idx_set["grid_key"]])
            mags = hdf5[grid_loc + "/Magnitude"].value
            mmax = hdf5[grid_loc + "/MMax"][background_sids]
            rates = hdf5[grid_loc + "/RateArray"][background_sids, :]
            locations = hdf5["Grid/Locations"][background_sids, :]
            sources = []
            for i, bg_idx in enumerate(background_sids):
                src_id = "_".join([self.idx_set["grid_key"], str(bg_idx)])
                src_name = "|".join([self.idx_set["total_key"], str(bg_idx)])
                # Get MFD
                mag_idx = numpy.logical_and(
                    mags >= ctl.min_mag, mags < mmax[i])
                src_mags = mags[mag_idx]
                src_rates = rates[i, :]
                src_mfd = EvenlyDiscretizedMFD(
                    src_mags[0], src_mags[1] - src_mags[0],
                    src_rates[mag_idx].tolist())
                ps = PointSource(
                    src_id, src_name, ctl.tectonic_region_type, src_mfd,
                    ctl.mesh_spacing, ctl.msr, ctl.aspect, ctl.tom, ctl.usd,
                    ctl.lsd, Point(locations[i, 0], locations[i, 1]),
                    ctl.npd, ctl.hdd)
                sources.append(ps)
        return sources


def build_idx_set(branch_id, start_date):
    """
    Builds a dictionary of indices based on the branch code
    """
    code_set = branch_id.split("/")
    idx_set = {
        "sec_idx": "/".join([code_set[0], code_set[1], "Sections"]),
        "mag_idx": "/".join([code_set[0], code_set[1], code_set[2],
                             "Magnitude"])}
    code_set.insert(3, "Rates")
    idx_set["rate_idx"] = "/".join(code_set)
    idx_set["rake_idx"] = "/".join([code_set[0], code_set[1], "Rake"])
    idx_set["msr_idx"] = "-".join([code_set[0], code_set[1], code_set[2]])
    idx_set["geol_idx"] = code_set[0]
    if start_date:  # time-dependent source
        idx_set["grid_key"] = "_".join(
            branch_id.replace("/", "_").split("_")[:-1])
    else:  # time-independent source
        idx_set["grid_key"] = branch_id.replace("/", "_")
    idx_set["total_key"] = branch_id.replace("/", "|")
    return idx_set

# #################################################################### #


@util.reader
def compute_ruptures(sources, src_filter, gsims, param, monitor):
    """
    :param sources: a list with a single UCERF source
    :param src_filter: a SourceFilter instance
    :param gsims: a list of GSIMs
    :param param: extra parameters
    :param monitor: a Monitor instance
    :returns: an AccumDict grp_id -> EBRuptures
    """
    [src] = sources
    res = AccumDict()
    res.calc_times = AccumDict()
    serial = 1
    sampl_mon = monitor('sampling ruptures', measuremem=True)
    filt_mon = monitor('filtering ruptures', measuremem=False)
    res.trt = DEFAULT_TRT
    t0 = time.time()
    ebruptures = []
    background_sids = src.get_background_sids(src_filter)
    sitecol = src_filter.sitecol
    idist = src_filter.integration_distance
    for sample in range(param['samples']):
        for ses_idx, ses_seed in param['ses_seeds']:
            seed = sample * event_based.TWO16 + ses_seed
            with sampl_mon:
                rups, n_occs = src.generate_event_set(
                    background_sids, src_filter, seed)
            with filt_mon:
                for rup, n_occ in zip(rups, n_occs):
                    rup.seed = seed
                    try:
                        r_sites, rrup = idist.get_closest(sitecol, rup)
                    except FarAwayRupture:
                        continue
                    indices = r_sites.indices
                    events = []
                    for _ in range(n_occ):
                        events.append((0, ses_idx, sample))
                    if events:
                        evs = numpy.array(events, calc.event_dt)
                        ebruptures.append(
                            calc.EBRupture(rup, indices, evs,
                                           src.src_group_id, serial))
                        serial += 1
    res.num_events = event_based.set_eids(
        ebruptures, getattr(monitor, 'task_no', 0))
    res[src.src_group_id] = ebruptures
    res.calc_times[src.src_group_id] = (
        src.source_id, len(sitecol), time.time() - t0)
    if not param['save_ruptures']:
        res.events_by_grp = {grp_id: event_based.get_events(res[grp_id])
                             for grp_id in res}
    res.eff_ruptures = {src.src_group_id: src.num_ruptures}
    return res


def get_composite_source_model(oq):
    """
    :param oq: :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns: a `class:`openquake.commonlib.source.CompositeSourceModel`
    """
    gsim_lt = readinput.get_gsim_lt(oq, [DEFAULT_TRT])
    smlt = readinput.get_source_model_lt(oq)
    [src_group] = nrml.parse(
        oq.inputs["source_model"],
        SourceConverter(oq.investigation_time, oq.rupture_mesh_spacing))
    [src] = src_group
    source_models = []
    for sm in smlt.gen_source_models(gsim_lt):
        sg = copy.copy(src_group)
        sg.id = sm.ordinal
        sm.src_groups = [sg]
        sg.sources = [UcerfSource(sg[0], sm.ordinal, sm.path[0], sm.name)]
        source_models.append(sm)
    return source.CompositeSourceModel(gsim_lt, smlt, source_models)


@base.calculators.add('ucerf_rupture')
class UCERFRuptureCalculator(event_based.EventBasedRuptureCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    core_task = compute_ruptures

    def pre_execute(self):
        """
        parse the logic tree and source model input
        """
        logging.warn('%s is still experimental', self.__class__.__name__)
        oq = self.oqparam
        self.read_risk_data()  # read the site collection
        self.src_filter = SourceFilter(self.sitecol, oq.maximum_distance)
        self.csm = get_composite_source_model(oq)
        logging.info('Found %d source model logic tree branches',
                     len(self.csm.source_models))
        self.datastore['csm_info'] = self.csm_info = self.csm.info
        self.rlzs_assoc = self.csm_info.get_rlzs_assoc()
        self.infos = []
        self.eid = collections.Counter()  # sm_id -> event_id
        self.sm_by_grp = self.csm_info.get_sm_by_grp()
        if not self.oqparam.imtls:
            raise ValueError('Missing intensity_measure_types!')
        self.rupser = calc.RuptureSerializer(self.datastore)

    def gen_args(self, csm, monitor):
        """
        Generate a task for each branch
        """
        oq = self.oqparam
        allargs = []  # it is better to return a list; if there is single
        # branch then `parallel.Starmap` will run the task in core
        for sm_id in range(len(csm.source_models)):
            ssm = csm.get_model(sm_id)
            [sm] = ssm.source_models
            gsims = ssm.gsim_lt.values[DEFAULT_TRT]
            srcs = ssm.get_sources()
            for ses_idx in range(1, oq.ses_per_logic_tree_path + 1):
                ses_seeds = [(ses_idx, oq.ses_seed + ses_idx)]
                param = dict(ses_seeds=ses_seeds, samples=sm.samples,
                             save_ruptures=oq.save_ruptures)
                allargs.append((srcs, self.src_filter, gsims, param, monitor))
        return allargs


class List(list):
    """Trivial container returned by compute_losses"""


@util.reader
def compute_losses(ssm, src_filter, param, riskmodel,
                   imts, trunc_level, correl_model, min_iml, monitor):
    """
    Compute the losses for a single source model. Returns the ruptures
    as an attribute `.ruptures_by_grp` of the list of losses.

    :param ssm: CompositeSourceModel containing a single source model
    :param sitecol: a SiteCollection instance
    :param param: a dictionary of parameters
    :param riskmodel: a RiskModel instance
    :param imts: a list of Intensity Measure Types
    :param trunc_level: truncation level
    :param correl_model: correlation model
    :param min_iml: vector of minimum intensities, one per IMT
    :param monitor: a Monitor instance
    :returns: a List containing the losses by taxonomy and some attributes
    """
    [grp] = ssm.src_groups
    res = List()
    gsims = ssm.gsim_lt.values[DEFAULT_TRT]
    ruptures_by_grp = compute_ruptures(
        grp, src_filter, gsims, param, monitor)
    [(grp_id, ebruptures)] = ruptures_by_grp.items()
    rlzs_assoc = ssm.info.get_rlzs_assoc()
    num_rlzs = len(rlzs_assoc.realizations)
    rlzs_by_gsim = rlzs_assoc.get_rlzs_by_gsim(grp_id)
    getter = riskinput.GmfGetter(
        grp_id, rlzs_by_gsim, ebruptures, src_filter.sitecol, imts, min_iml,
        trunc_level, correl_model, rlzs_assoc.samples[grp_id])
    ri = riskinput.RiskInputFromRuptures(getter)
    res.append(event_based_risk(ri, riskmodel, param, monitor))
    res.sm_id = ssm.sm_id
    res.num_events = len(ri.hazard_getter.eids)
    start = res.sm_id * num_rlzs
    res.rlz_slice = slice(start, start + num_rlzs)
    res.events_by_grp = ruptures_by_grp.events_by_grp
    return res


@base.calculators.add('ucerf_hazard')
class UCERFHazardCalculator(event_based.EventBasedCalculator):
    """
    Runs a standard event based calculation starting from UCERF ruptures
    """
    pre_calculator = 'ucerf_rupture'


@base.calculators.add('ucerf_risk')
class UCERFRiskCalculator(EbriskCalculator):
    """
    Event based risk calculator for UCERF, parallelizing on the source models
    """
    pre_execute = UCERFRuptureCalculator.__dict__['pre_execute']

    def gen_args(self):
        """
        Yield the arguments required by build_ruptures, i.e. the
        source models, the asset collection, the riskmodel and others.
        """
        oq = self.oqparam
        self.L = len(self.riskmodel.lti)
        self.I = oq.insured_losses + 1
        correl_model = oq.get_correl_model()
        min_iml = self.get_min_iml(oq)
        imts = list(oq.imtls)
        elt_dt = numpy.dtype([('eid', U64), ('loss', (F32, (self.L, self.I)))])
        monitor = self.monitor('compute_losses')
        for sm in self.csm.source_models:
            ssm = self.csm.get_model(sm.ordinal)
            for ses_idx in range(1, oq.ses_per_logic_tree_path + 1):
                param = dict(ses_seeds=[(ses_idx, oq.ses_seed + ses_idx)],
                             samples=1, assetcol=self.assetcol,
                             save_ruptures=False,
                             ses_ratio=oq.ses_ratio,
                             avg_losses=oq.avg_losses,
                             loss_ratios=oq.loss_ratios,
                             elt_dt=elt_dt,
                             asset_loss_table=False,
                             insured_losses=oq.insured_losses)
                yield (ssm, self.src_filter, param,
                       self.riskmodel, imts, oq.truncation_level,
                       correl_model, min_iml, monitor)

    def execute(self):
        num_rlzs = len(self.rlzs_assoc.realizations)
        self.grp_trt = self.csm_info.grp_trt()
        res = parallel.Starmap(compute_losses, self.gen_args()).submit_all()
        self.vals = self.assetcol.values()
        num_events = self.save_results(res, num_rlzs)
        return num_events
