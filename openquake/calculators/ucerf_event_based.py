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
import socket
import collections
import h5py
import numpy

from openquake.baselib.general import AccumDict
from openquake.baselib.python3compat import zip
from openquake.baselib import parallel
from openquake.hazardlib import nrml
from openquake.risklib import riskinput
from openquake.commonlib import readinput, source, calc, config, logictree
from openquake.calculators import base, event_based
from openquake.calculators.event_based_risk import (
    EbriskCalculator, build_el_dtypes, event_based_risk)

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
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.mfd import EvenlyDiscretizedMFD
from openquake.hazardlib.sourceconverter import SourceConverter


# ######################## rupture calculator ############################ #

U16 = numpy.uint16
U32 = numpy.uint32
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


def prefilter_ruptures(hdf5, ridx, idx_set, sites, integration_distance):
    """
    Determines if a rupture is likely to be inside the integration distance
    by considering the set of fault plane centroids.

    :param hdf5:
        Source of UCERF file as h5py.File object
    :param list ridx:
        List of indices composing the rupture sections
    :param dict idx_set:
        Set of indices for the branch
    :param sites:
        Sites for consideration (can be None!)
    :param float integration_distance:
        Maximum distance from rupture to site for consideration
    """
    # Generate array of sites
    if not sites:
        return True
    centroids = numpy.array([[0., 0., 0.]], dtype="f")
    for idx in ridx:
        trace_idx = "{:s}/{:s}".format(idx_set["sec_idx"], str(idx))
        centroids = numpy.vstack([
            centroids,
            hdf5[trace_idx + "/Centroids"][:].astype("float64")])
    centroids = centroids[1:, :]
    distance = min_geodetic_distance(centroids[:, 0], centroids[:, 1],
                                     sites.lons, sites.lats)
    return numpy.any(distance <= integration_distance)


def get_ucerf_rupture(hdf5, iloc, idx_set, tom, src_filter,
                      mesh_spacing=DEFAULT_MESH_SPACING,
                      trt=DEFAULT_TRT):
    """
    :param hdf5:
        Source Model hdf5 object as instance of :class: h5py.File
    :param int iloc:
        Location of the rupture plane in the hdf5 file
    :param dict idx_set:
        Set of indices for the branch
    :param tom:
        Temporal occurrence model as instance of :class:
        openquake.hazardlib.tom.TOM
    :param src_filter:
        Sites for consideration and maximum distance
    """
    ridx = hdf5[idx_set["geol_idx"] + "/RuptureIndex"][iloc]
    surface_set = []
    integration_distance = src_filter.integration_distance[DEFAULT_TRT]
    if not prefilter_ruptures(
            hdf5, ridx, idx_set, src_filter.sitecol, integration_distance):
        return None, None
    for idx in ridx:
        # Build simple fault surface
        trace_idx = "{:s}/{:s}".format(idx_set["sec_idx"], str(idx))
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
                surface_set.append(ImperfectPlanarSurface.from_corner_points(
                    mesh_spacing,
                    top_left,
                    top_right,
                    bottom_right,
                    bottom_left))
            except ValueError as evl:
                raise ValueError(evl, trace_idx, top_left, top_right,
                                 bottom_right, bottom_left)

    rupture = ParametricProbabilisticRupture(
        hdf5[idx_set["mag_idx"]][iloc],  # Magnitude
        hdf5[idx_set["rake_idx"]][iloc],  # Rake
        trt,  # Tectonic Region Type
        surface_set[len(surface_set) // 2].get_middle_point(),  # Hypocentre
        MultiSurface(surface_set),
        CharacteristicFaultSource,
        hdf5[idx_set["rate_idx"]][iloc],  # Rate of events
        tom)

    # Get rupture index code string
    ridx_string = "-".join(str(val) for val in ridx)
    return rupture, ridx_string


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


def prefilter_background_model(hdf5, branch_key, sites, integration_distance,
                               msr=WC1994(), aspect=1.5):
    """
    Identify those points within the integration distance

    :param sites:
        Sites under consideration
    :param float integration_distance:
        Maximum distance from rupture to site for consideration
    :param msr:
        Magnitude scaling relation
    :param float aspect:
        Aspect ratio
    :returns:
        List of site IDs within the integration distance
    """
    bg_locations = hdf5["Grid/Locations"][:].astype("float64")
    n_locations = bg_locations.shape[0]
    distances = min_idx_dst(sites.lons, sites.lats,
                            numpy.zeros_like(sites.lons),
                            bg_locations[:, 0],
                            bg_locations[:, 1],
                            numpy.zeros(n_locations))[1]
    # Add buffer equal to half of length of median area from Mmax
    mmax_areas = msr.get_median_area(
        hdf5["/".join(["Grid", branch_key, "MMax"])][:], 0.0)
    # for instance hdf5['Grid/FM0_0_MEANFS_MEANMSR/MMax']
    mmax_lengths = numpy.sqrt(mmax_areas / aspect)
    ok = distances <= (0.5 * mmax_lengths + integration_distance)
    # get list of indices from array of booleans
    return numpy.where(ok)[0].tolist()


def sample_background_model(
        hdf5, branch_key, tom, filter_idx, min_mag, npd, hdd,
        upper_seismogenic_depth, lower_seismogenic_depth, msr=WC1994(),
        aspect=1.5, trt=DEFAULT_TRT):
    """
    Generates a rupture set from a sample of the background model

    :param branch_key:
        Key to indicate the branch for selecting the background model
    :param tom:
        Temporal occurrence model as instance of :class:
        openquake.hazardlib.tom.TOM
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
    bg_magnitudes = hdf5["/".join(["Grid", branch_key, "Magnitude"])][:]
    # Select magnitudes above the minimum magnitudes
    mag_idx = bg_magnitudes >= min_mag
    mags = bg_magnitudes[mag_idx]
    # Filter out sites beyond integration distance
    # valid_idx = prefilter_background_model(sites, integration_distance, msr)
    rates = hdf5["/".join(["Grid", branch_key, "RateArray"])][filter_idx, :]
    rates = rates[:, mag_idx]
    valid_locs = hdf5["Grid/Locations"][filter_idx, :]
    # Sample remaining rates
    sampler = tom.sample_number_of_occurrences(rates)
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
    def __init__(self, control, grp_id, branch_name, branch_id):
        self.control = control
        self.src_group_id = grp_id
        self.source_id = branch_name
        self.idx_set = build_idx_set(branch_id, control.start_date)
        with h5py.File(self.control.source_file, "r") as hdf5:
            self.num_ruptures = len(hdf5[self.idx_set["rate_idx"]])

    @property
    def weight(self):
        """
        Weight of the source, equal to the number of ruptures contained
        """
        return self.num_ruptures

    def get_background_sids(self, src_filter):
        """
        We can apply the filtering of the background sites as a pre-processing
        step - this is done here rather than in the sampling of the ruptures
        themselves
        """
        ctl = self.control
        integration_distance = src_filter.integration_distance[DEFAULT_TRT]
        with h5py.File(ctl.source_file, 'r') as hdf5:
            return prefilter_background_model(
                hdf5, self.idx_set["grid_key"], src_filter.sitecol,
                integration_distance, ctl.msr, ctl.aspect)

    def generate_event_set(self, background_sids, src_filter):
        """
        Generates the event set corresponding to a particular branch
        """
        # get rates from file
        ctl = self.control
        with h5py.File(ctl.source_file, 'r') as hdf5:
            rates = hdf5[self.idx_set["rate_idx"]].value
            occurrences = ctl.tom.sample_number_of_occurrences(rates)
            indices = numpy.where(occurrences)[0]
            logging.debug(
                'Considering "%s", %d ruptures', self.source_id, len(indices))

            # get ruptures from the indices
            ruptures = []
            rupture_occ = []
            for idx, n_occ in zip(indices, occurrences[indices]):
                ucerf_rup, _ = get_ucerf_rupture(
                    hdf5, idx, self.idx_set, ctl.tom, src_filter,
                    ctl.mesh_spacing, ctl.tectonic_region_type)

                if ucerf_rup:
                    ruptures.append(ucerf_rup)
                    rupture_occ.append(n_occ)

            # sample background sources
            background_ruptures, background_n_occ = sample_background_model(
                hdf5, self.idx_set["grid_key"], ctl.tom, background_sids,
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
            try:  # the task has set a subset of indices
                rupset_idx = self.rupset_idx
            except AttributeError:  # use all indices
                rupset_idx = numpy.arange(self.num_ruptures)
            rate = hdf5[self.idx_set["rate_idx"]]
            for ridx in rupset_idx:
                # Get the ucerf rupture rate from the MeanRates array
                if not rate[ridx]:
                    # ruptures may have have zero rate
                    continue
                rup, ridx_string = get_ucerf_rupture(
                    hdf5, ridx,
                    self.idx_set,
                    ctl.tom,
                    self.src_filter,
                    ctl.mesh_spacing,
                    ctl.tectonic_region_type)
                if rup:
                    yield rup

    def get_background_sources(self, background_sids):
        """
        Turn the background model of a given branch into a set of point sources

        :param background_sids:
            Site IDs affected by the background sources
        """
        ctl = self.control
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

    def filter_sites_by_distance_from_rupture_set(
            self, rupset_idx, sites, max_dist):
        """
        Filter sites by distances from a set of ruptures
        """
        with h5py.File(self.control.source_file, "r") as hdf5:
            rup_index_key = "/".join([self.idx_set["geol_idx"],
                                      "RuptureIndex"])

            # Find the combination of rupture sections used in this model
            rupture_set = set()
            # Determine which of the rupture sections used in this set
            # of indices
            rup_index = hdf5[rup_index_key]
            for i in rupset_idx:
                rupture_set.update(rup_index[i])
            centroids = numpy.empty([1, 3])
            # For each of the identified rupture sections, retreive the
            # centroids
            for ridx in rupture_set:
                trace_idx = "{:s}/{:s}".format(self.idx_set["sec_idx"],
                                               str(ridx))
                centroids = numpy.vstack([
                    centroids,
                    hdf5[trace_idx + "/Centroids"][:].astype("float64")])
            distance = min_geodetic_distance(centroids[1:, 0],
                                             centroids[1:, 1],
                                             sites.lons, sites.lats)
            idx = distance <= max_dist
            if numpy.any(idx):
                return rupset_idx, sites.filter(idx)
            else:
                return [], []


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


def compute_ruptures(sources, src_filter, gsims, monitor):
    """
    :param sources: a sequence of UCERF sources
    :param src_filter: a SourceFilter instance
    :param gsims: a list of GSIMs
    :param monitor: a Monitor instance
    :returns: an AccumDict grp_id -> EBRuptures
    """
    [src] = sources  # there is a single source per UCERF branch
    res = AccumDict()
    res.calc_times = AccumDict()
    serial = 1
    event_mon = monitor('sampling ruptures', measuremem=False)
    res.num_events = 0
    res.trt = DEFAULT_TRT
    t0 = time.time()
    # set the seed before calling generate_event_set
    numpy.random.seed(monitor.seed + src.src_group_id)
    ebruptures = []
    eid = 0
    integration_distance = src_filter.integration_distance[DEFAULT_TRT]
    background_sids = src.get_background_sids(src_filter)
    sitecol = src_filter.sitecol
    for ses_idx in range(1, monitor.ses_per_logic_tree_path + 1):
        with event_mon:
            rups, n_occs = src.generate_event_set(background_sids, src_filter)
        for rup, n_occ in zip(rups, n_occs):
            rup.seed = monitor.seed  # to think
            rrup = rup.surface.get_min_distance(sitecol.mesh)
            r_sites = sitecol.filter(rrup <= integration_distance)
            if r_sites is None:
                continue
            indices = r_sites.indices
            events = []
            for occ in range(n_occ):
                events.append((eid, ses_idx, occ, 0))  # 0 is the sampling
                eid += 1
            if events:
                evs = numpy.array(events, calc.event_dt)
                ebruptures.append(
                    calc.EBRupture(rup, indices, evs, src.source_id,
                                   src.src_group_id, serial))
                serial += 1
                res.num_events += len(events)
    res[src.src_group_id] = ebruptures
    res.calc_times[src.src_group_id] = (
        src.source_id, len(sitecol), time.time() - t0)
    if monitor.save_ruptures:
        res.rup_data = {src.src_group_id: calc.RuptureData(DEFAULT_TRT, gsims)
                        .to_array(ebruptures)}
    return res
compute_ruptures.shared_dir_on = config.SHARED_DIR_ON


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
        self.gsim_lt = readinput.get_gsim_lt(oq, [DEFAULT_TRT])
        self.smlt = readinput.get_source_model_lt(oq)
        job_info = dict(hostname=socket.gethostname())
        self.datastore.save('job_info', job_info)
        parser = nrml.SourceModelParser(
            SourceConverter(oq.investigation_time, oq.rupture_mesh_spacing))
        [src_group] = parser.parse_src_groups(oq.inputs["source_model"])
        [src] = src_group
        branches = sorted(self.smlt.branches.items())
        source_models = []
        num_gsim_paths = self.gsim_lt.get_num_paths()
        for grp_id, rlz in enumerate(self.smlt):
            [name] = rlz.lt_path
            sg = copy.copy(src_group)
            sg.id = grp_id
            # i.e, branch_name='ltbr0001'
            # branch_id='FM3_1/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2'
            sg.sources = [UcerfSource(src, grp_id, name, rlz.value)]
            sm = logictree.SourceModel(
                name, rlz.weight, [name], [sg], num_gsim_paths, grp_id, 1)
            source_models.append(sm)
        self.csm = source.CompositeSourceModel(
            self.gsim_lt, self.smlt, source_models, set_weight=True)
        self.datastore['csm_info'] = self.csm.info
        logging.info('Found %d x %d logic tree branches', len(branches),
                     self.gsim_lt.get_num_paths())
        self.rlzs_assoc = self.csm.info.get_rlzs_assoc()
        self.infos = []
        self.eid = collections.Counter()  # sm_id -> event_id
        self.sm_by_grp = self.csm.info.get_sm_by_grp()
        if not self.oqparam.imtls:
            raise ValueError('Missing intensity_measure_types!')

    def gen_args(self, csm, monitor):
        """
        Generate a task for each branch
        """
        oq = self.oqparam
        allargs = []  # it is better to return a list; if there is single
        # branch then `parallel.Starmap` will run the task in core
        for sm_id in range(len(csm.source_models)):
            ssm = csm.get_model(sm_id)
            mon = monitor.new(
                ses_per_logic_tree_path=oq.ses_per_logic_tree_path,
                maximum_distance=oq.maximum_distance,
                samples=ssm.source_models[0].samples,
                save_ruptures=oq.save_ruptures,
                seed=ssm.source_model_lt.seed)
            gsims = ssm.gsim_lt.values[DEFAULT_TRT]
            allargs.append((ssm.get_sources(), self.src_filter, gsims, mon))
        return allargs


class List(list):
    """Trivial container returned by compute_losses"""


def compute_losses(ssm, src_filter, assetcol, riskmodel,
                   imts, trunc_level, correl_model, min_iml, monitor):
    """
    Compute the losses for a single source model. Returns the ruptures
    as an attribute `.ruptures_by_grp` of the list of losses.

    :param ssm: CompositeSourceModel containing a single source model
    :param sitecol: a SiteCollection instance
    :param assetcol: an AssetCollection instance
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
    res.ruptures_by_grp = compute_ruptures(grp, src_filter, gsims, monitor)
    [(grp_id, ebruptures)] = res.ruptures_by_grp.items()
    rlzs_assoc = ssm.info.get_rlzs_assoc()
    num_rlzs = len(rlzs_assoc.realizations)
    ri = riskinput.RiskInputFromRuptures(
        DEFAULT_TRT, rlzs_assoc, imts, src_filter.sitecol, ebruptures,
        trunc_level, correl_model, min_iml)
    res.append(event_based_risk(ri, riskmodel, assetcol, monitor))
    res.sm_id = ssm.sm_id
    res.num_events = len(ri.eids)
    start = res.sm_id * num_rlzs
    res.rlz_slice = slice(start, start + num_rlzs)
    return res
compute_losses.shared_dir_on = config.SHARED_DIR_ON


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
        correl_model = oq.get_correl_model()
        min_iml = self.get_min_iml(oq)
        imts = list(oq.imtls)
        ela_dt, elt_dt = build_el_dtypes(
            self.riskmodel.loss_types, oq.insured_losses)
        for sm in self.csm.source_models:
            monitor = self.monitor.new(
                ses_ratio=oq.ses_ratio,
                ela_dt=ela_dt, elt_dt=elt_dt,
                loss_ratios=oq.loss_ratios,
                avg_losses=oq.avg_losses,
                insured_losses=oq.insured_losses,
                ses_per_logic_tree_path=oq.ses_per_logic_tree_path,
                maximum_distance=oq.maximum_distance,
                samples=sm.samples,
                save_ruptures=oq.save_ruptures,
                seed=self.oqparam.random_seed)
            ssm = self.csm.get_model(sm.ordinal)
            yield (ssm, self.src_filter, self.assetcol, self.riskmodel,
                   imts, oq.truncation_level, correl_model, min_iml, monitor)

    def execute(self):
        num_rlzs = len(self.rlzs_assoc.realizations)
        self.grp_trt = self.csm.info.grp_trt()
        allres = parallel.Starmap(compute_losses, self.gen_args()).submit_all()
        num_events = self.save_results(allres, num_rlzs)
        self.save_data_transfer(allres)
        return num_events
