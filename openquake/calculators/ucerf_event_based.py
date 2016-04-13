# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2016 GEM Foundation
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
import time
import os.path
import operator
import logging
import collections

import h5py
import numpy
import math
import random

from openquake.baselib.general import AccumDict
from openquake.baselib.python3compat import zip
from openquake.commonlib import readinput, parallel, datastore, valid, source

from openquake.calculators import base, views, event_based
from openquake.calculators.classical import ClassicalCalculator


from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.geodetic import (
    min_distance, min_geodetic_distance)
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.hazardlib.source.characteristic import CharacteristicFaultSource
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.scalerel.wc1994 import WC1994

from openquake.calculators.calc import MAX_INT
from openquake.commonlib.sourceconverter import SourceConverter


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


def prefilter_ruptures(fle, ridx, idx_set, sites, integration_distance):
    """
    Determines if a rupture is likely to be inside the integration distance
    by considering the set of fault plane centroids
    :param fle:
        Source of UCERF HDF5 file (as h5py.File object)
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
            fle[trace_idx + "/Centroids"][:].astype("float64")])
    centroids = centroids[1:, :]
    distance = min_geodetic_distance(centroids[:, 0], centroids[:, 1],
                                     sites.lons, sites.lats)
    return numpy.any(distance <= integration_distance)


def get_ucerf_rupture(hdf5, iloc, idx_set, tom, sites,
                      integration_distance, mesh_spacing=DEFAULT_MESH_SPACING,
                      trt=DEFAULT_TRT):
    """
    :param hdf5:
        Source Model hdf5 object as instance of :class: h5py.File
    :param int iloc:
        Location of the rupture plane in the hdf5 file
    :param dict idx_set:
        Set of indices for the branch
    Generates a rupture set from a sample of the background model
    :param tom:
        Temporal occurrence model as instance of :class:
        openquake.hazardlib.tom.TOM
    :param sites:
        Sites for consideration (can be None!)
    """
    ridx = hdf5[idx_set["geol_idx"] + "/RuptureIndex"][iloc]
    surface_set = []
    if not prefilter_ruptures(
            hdf5, ridx, idx_set, sites, integration_distance):
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
                surface_set.append(PlanarSurface.from_corner_points(
                    mesh_spacing,
                    top_left,
                    top_right,
                    bottom_right,
                    bottom_left))
            except ValueError as evl:
                print evl, trace_idx, top_left, top_right, bottom_right,\
                    bottom_left
                raise ValueError
    rupture = ParametricProbabilisticRupture(
        hdf5[idx_set["mag_idx"]][iloc],  # Magnitude
        hdf5[idx_set["rake_idx"]][iloc],  # Rake
        trt,
        surface_set[len(surface_set)/2].get_middle_point(),  # Hypocentre
        MultiSurface(surface_set),
        CharacteristicFaultSource,
        hdf5[idx_set["rate_idx"]][iloc],  # Rate of events
        tom)
    # Get rupture index code string
    ridx_string = "-".join([str(val) for val in ridx])
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
    assert upper_seismogenic_depth <= hypocenter.depth \
        and lower_seismogenic_depth >= hypocenter.depth
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
    rupture_set = []
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
        rupture_set.append(ParametricProbabilisticRupture(
            mag, nodal_planes[i][1].rake, trt, hypocentre, surface,
            PointSource, rupture_probability, tom))
    return rupture_set


def prefilter_background_model(hdf5, sites, integration_distance, msr=WC1994(),
                               aspect=1.5):
    """
    Identify those points within the integration distance
    :param sites:
        Sites for consideration (can be None!)
    :param float integration_distance:
        Maximum distance from rupture to site for consideration
    :param msr:
        Magnitude scaling relation
    :param float aspect:
        Aspect ratio
    :returns:
        Boolean vector indicating if sites are within (True) or outside (False)
        the integration distance
    """
    bg_locations = hdf5["Grid/Locations"][:].astype("float64")
    n_locations = bg_locations.shape[0]
    if not sites:
        # Apply no filtering - all sources valid
        return numpy.ones(n_locations, dtype=bool)
    distances = min_distance(sites.lons, sites.lats,
                             numpy.zeros_like(sites.lons),
                             bg_locations[:, 0],
                             bg_locations[:, 1],
                             numpy.zeros(n_locations))
    # Add buffer equal to half of length of median area from Mmax
    mmax_areas = msr.get_median_area(hdf5["Grid/MMax"][:], 0.0)
    mmax_lengths = numpy.sqrt(mmax_areas / aspect)
    return distances <= (0.5 * mmax_lengths + integration_distance)


def sample_background_model(
        hdf5, tom, filter_idx, min_mag, npd, hdd,
        upper_seismogenic_depth, lower_seismogenic_depth, msr=WC1994(),
        aspect=1.5, trt=DEFAULT_TRT):
    """
    Generates a rupture set from a sample of the background model
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
    bg_magnitudes = hdf5["Grid/Magnitudes"][:]
    # Select magnitudes above the minimum magnitudes
    mag_idx = bg_magnitudes >= min_mag
    mags = bg_magnitudes[mag_idx]
    # Filter out sites beyond integration distance
    # valid_idx = prefilter_background_model(sites, integration_distance, msr)
    rates = hdf5["Grid/RateArray"][filter_idx, :]
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
        rupture_set = generate_background_ruptures(
            tom, locations, occurrence,
            mag, npd, hdd, upper_seismogenic_depth,
            lower_seismogenic_depth, msr, aspect, trt)
        background_ruptures.extend(rupture_set)
        background_n_occ.extend(rate_cnt.tolist())
    return background_ruptures, background_n_occ


class UCERFSESControl(object):
    """
        :param str branch:
            Valid branch of UCERF
        :param sites:
            Sites for consideration of events as instance of :class:
            openquake.hazardlib.site.SiteCollection
        :param float investigation_time:
            Investigation time of event set (years)
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
    def __init__(self, source_file, id, investigation_time, min_mag,
                 npd=NPD, hdd=HDD, aspect=1.5,
                 upper_seismogenic_depth=0.0, lower_seismogenic_depth=15.,
                 msr=WC1994(), mesh_spacing=1.0, trt="Active Shallow Crust"):
        assert os.path.exists(source_file)
        self.source_file = source_file
        self.source_id = id
        self.inv_time = investigation_time
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
        self.seed = random.randint(0, MAX_INT)
        self.rnd = None
        self.integration_distance = 1000
        self.sites = None
        self.background_idx = None
        self.num_ruptures = 0

    def update_background_site_filter(self, sites, integration_distance=1000.):
        """
        We can apply the filtering of the background sites as a pre-processing
        step - this is done here rather than in the sampleing of the ruptures
        themselves
        """
        self.sites = sites
        self.integration_distance = integration_distance
        hdf5 = h5py.File(self.source_file)
        self.background_idx = prefilter_background_model(
            hdf5,
            self.sites,
            integration_distance,
            self.msr,
            self.aspect)
        hdf5.close()

    def get_min_max_mag(self):
        """
        To mirror the behaviour of a :class:
        openquake.hazardlib.source.BaseSeismicSource this returns the
        minimum magnitude and None
        """
        return self.min_mag, None

    def update_seed(self, seed):
        """
        Updates the random seed associated with the source
        """
        self.rnd = random.Random(seed)

    def _get_tom(self):
        """
        Returns the temporal occurence model as a Poisson TOM
        """
        return PoissonTOM(self.inv_time)

    def __len__(self):
        return 1

    def generate_event_set(self, branch_id, sites=None,
                           integration_distance=1000.):
        """
        Generates the event set corresponding to a particular branch

        """
        if sites:
            self.update_background_site_filter(sites, integration_distance)
        idxset = self.build_idx_set(branch_id)
        # Get rates from file
        hdf5 = h5py.File(self.source_file, "r+")
        rates = hdf5[idxset["rate_idx"]][:]
        occurrences = self.tom.sample_number_of_occurrences(rates)
        indices = numpy.where(occurrences)[0]
        print branch_id, indices
        # Get ruptures from the indices
        rupture_set = []
        rupture_occ = []
        for idx, n_occ in zip(indices, occurrences[indices]):
            ucerf_rup, _ = get_ucerf_rupture(
                hdf5, idx, idxset, self.tom, self.sites,
                self.integration_distance, self.mesh_spacing,
                self.tectonic_region_type)
            if ucerf_rup:
                rupture_set.append(ucerf_rup)
                rupture_occ.append(n_occ)

        # Sample Background sources
        background_ruptures, background_n_occ = sample_background_model(
            hdf5,
            self.tom,
            self.background_idx,
            self.min_mag,
            self.npd, self.hdd,
            self.usd, self.lsd,
            self.msr, self.aspect,
            self.tectonic_region_type)
        rupture_set.extend(background_ruptures)
        rupture_occ.extend(background_n_occ)
        hdf5.close()
        return rupture_set, rupture_occ

    @staticmethod
    def build_idx_set(branch_code):
        """
        Builds a dictionary of indices based on the branch code
        :param str branch_code:
            Code for the branch
        """
        code_set = branch_code.split("/")
        ridx_loc = "/".join([code_set[0], "RuptureIndex"])
        idx_set = {
        "sec_idx": "/".join([code_set[0], code_set[1], "Sections"]),
        "mag_idx": "/".join([code_set[0], code_set[1], code_set[2],
                             "Magnitude"])}
        code_set.insert(3, "Rates")
        idx_set["rate_idx"] = "/".join(code_set)
        idx_set["rake_idx"] = "/".join([code_set[0], code_set[1], "Rake"])
        idx_set["msr_idx"] = "-".join([code_set[0], code_set[1], code_set[2]])
        idx_set["geol_idx"] = code_set[0]
        idx_set["total_key"] = branch_code.replace("/", "|")
        return idx_set


def num_affected_sites(rupture, num_sites):
    """
    :param rupture: a EBRupture object
    :param num_sites: the total number of sites
    :returns: the number of sites affected by the rupture
    """
    return (len(rupture.indices) if rupture.indices is not None
            else num_sites)


def get_site_ids(rupture, num_sites):
    """
    :param rupture: a EBRupture object
    :param num_sites: the total number of sites
    :returns: the indices of the sites affected by the rupture
    """
    if rupture.indices is None:
        return list(range(num_sites))
    return rupture.indices


@datastore.view.add('col_rlz_assocs')
def view_col_rlz_assocs(name, dstore):
    """
    :returns: an array with the association array col_ids -> rlz_ids
    """
    rlzs_assoc = dstore['rlzs_assoc']
    num_ruptures = dstore.get_attr('etags', 'num_ruptures')
    num_rlzs = len(rlzs_assoc.realizations)
    col_ids_list = [[] for _ in range(num_rlzs)]
    for rlz in rlzs_assoc.realizations:
        for col_id in sorted(rlzs_assoc.get_col_ids(rlz)):
            if num_ruptures[col_id]:
                col_ids_list[rlz.ordinal].append(col_id)
    assocs = collections.defaultdict(list)
    for i, col_ids in enumerate(col_ids_list):
        assocs[tuple(col_ids)].append(i)
    tbl = [['Collections', 'Realizations']] + sorted(assocs.items())
    return views.rst_table(tbl)


# #################################################################### #


class UCERFSourceConverter(SourceConverter):
    """
    Adjustment of the UCERF Source Converter to return the source information
    as an instance of the UCERF SES Control object
    """
    def convert_UCERFSource(self, node):
        """
        Converts the Ucerf Source node into an SES Control object
        """
        msr = valid.SCALEREL[~node.magScaleRel]()
        return UCERFSESControl(
            node["filename"],
            node["id"],
            self.tom.time_span,
            float(node["minMag"]),
            npd=self.convert_npdist(node),
            hdd=self.convert_hpdist(node),
            aspect=~node.ruptAspectRatio,
            upper_seismogenic_depth=~node.pointGeometry.upperSeismoDepth,
            lower_seismogenic_depth=~node.pointGeometry.lowerSeismoDepth,
            msr=msr,
            mesh_spacing=self.rupture_mesh_spacing,
            trt=node["tectonicRegion"]
        )


@parallel.litetask
def compute_ruptures(branch_info, source, sitecol, oqparam, monitor):
    """
    Returns the ruptures as a TRT set
    :param str branch_info:
        Tuple of (ltbr, branch_id, branch_weight)
    :param source:
        Instance of the UCERFSESControl object
    :param sitecol:
        Site collection :class: openquake.hazardlib.site.SiteCollection
    :param info:
        Instance of the :class: openquake.commonlib.source.CompositionInfo
    :returns:
        Dictionary of rupture instances associated to a TRT ID
    """
    integration_distance = oqparam.maximum_distance["default"]
    res = AccumDict()
    res.calc_times = []
    serial = 1
    for trt_model_id, (ltbrid, branch_id, _) in enumerate(branch_info):
        t0 = time.time()
        ses_ruptures = []
        source.update_background_site_filter(sitecol, integration_distance)
        for ses_idx in range(1, oqparam.ses_per_logic_tree_path + 1):
            rups, n_occs = source.generate_event_set(branch_id, sitecol,
                                                     integration_distance)
            for i, rup in enumerate(rups):
                if sitecol:
                    rrup = rup.surface.get_min_distance(sitecol.mesh)
                    r_sites = sitecol.filter(rrup <= integration_distance)
                    indices = r_sites.indices
                else:
                    indices = None
                # Build tag
                etags = []
                for j in range(n_occs[i]):
                    etags.append("col=1~ses=%04d~src=%s~rup=%03d-%02d" % (
                        ses_idx, source.source_id, i, j))
                if len(etags):
                    ses_ruptures.append(
                        event_based.EBRupture(
                            rup, indices, etags, trt_model_id, serial))
                    serial += 1
            dt = time.time() - t0
            res.calc_times.append((ltbrid, dt))
        res[trt_model_id] = ses_ruptures
    res.trt = DEFAULT_TRT
    return res


@base.calculators.add('ucerf_event_based_rupture')
class UCERFEventBasedRuptureCalculator(ClassicalCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    core_task = compute_ruptures
    etags = datastore.persistent_attribute('etags')
    is_stochastic = True

    def pre_execute(self):
        """
        parse the logic tree and source model input
        """
        self.smlt = readinput.get_source_model_lt(self.oqparam)
        converter = UCERFSourceConverter(self.oqparam.investigation_time,
                                         self.oqparam.rupture_mesh_spacing)
        parser = source.SourceModelParser(converter)
        self.source = parser.parse_sources(
            self.oqparam.inputs["source_model"])[0]

    def execute(self):
        """
        Run the ucerf event based calculation
        """
        id_set = [(key, self.smlt.branches[key].value,
                  self.smlt.branches[key].weight)
                  for key in self.smlt.branches]
        ruptures_by_branch_id = parallel.apply_reduce(
            compute_ruptures, (id_set, self.source, None, self.oqparam,
                               self.monitor))
        return ruptures_by_branch_id

    def count_eff_ruptures(self, ruptures_by_trt_id, trt_model):
        """
        Returns the number of ruptures sampled in the given trt_model.

        :param ruptures_by_trt_id: a dictionary with key trt_id
        :param trt_model: a TrtModel instance
        """
        return sum(
            len(ruptures) for trt_id, ruptures in ruptures_by_trt_id.items()
            if trt_model.id == trt_id)

    def agg_curves(self, acc, val):
        """
        For the rupture calculator, increment the AccumDict trt_id -> ruptures
        """
        acc += val

    def zerodict(self):
        """
        Initial accumulator, a dictionary trt_model_id -> list of ruptures
        """
        smodels = self.rlzs_assoc.csm_info.source_models
        zd = AccumDict((tm.id, []) for smodel in smodels
                       for tm in smodel.trt_models)
        zd.calc_times = []
        return zd

    def send_sources(self):
        """
        Filter, split and set the seed array for each source, then send it the
        workers
        """
        oq = self.oqparam
        self.manager = self.SourceManager(
            self.csm, self.core_task.__func__,
            oq.maximum_distance, self.datastore,
            self.monitor.new(oqparam=oq), oq.random_seed, oq.filter_sources)
        self.manager.submit_sources(self.sitecol)

    def post_execute(self, result):
        """
        Save the SES collection
        """
        logging.info('Generated %d EBRuptures',
                     sum(len(v) for v in result.values()))
        with self.monitor('saving ruptures', autoflush=True):
            sescollection = [[] for _ in sorted(self.smlt.branches)]
            etags = []
            for trt_id in result:
                for ebr in result[trt_id]:
                    sescollection[trt_id].append(ebr)
                    etags.extend(ebr.etags)
            etags.sort()
            etag2eid = dict(zip(etags, range(len(etags))))
            self.etags = numpy.array(etags, (bytes, 100))
            self.datastore.set_attrs(
                'etags',
                num_ruptures=numpy.array([len(sc) for sc in sescollection]))
            for i, sescol in enumerate(sescollection):
                for ebr in sescol:
                    ebr.eids = [etag2eid[etag] for etag in ebr.etags]
                nr = len(sescol)
                logging.info('Saving SES collection #%d with %d ruptures',
                             i, nr)
                key = 'sescollection/trt=%02d' % i
                self.datastore[key] = sorted(
                    sescol, key=operator.attrgetter('serial'))
                self.datastore.set_attrs(key, num_ruptures=nr, trt_model_id=i)
