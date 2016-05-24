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
import operator
import math, random

from openquake.baselib.general import AccumDict
from openquake.baselib.python3compat import zip
from openquake.baselib.performance import Monitor
from openquake.hazardlib.calc.filters import \
    filter_sites_by_distance_to_rupture
from openquake.hazardlib.calc.hazard_curve import zero_curves
from openquake.hazardlib import geo, site, calc
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.commonlib import readinput, parallel, datastore, valid
from openquake.commonlib.util import max_rel_diff_index, Rupture

from openquake.calculators import base, views
from openquake.calculators.calc import gmvs_to_haz_curve
from openquake.calculators.classical import ClassicalCalculator


from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.geodetic import (min_distance, 
                                              geodetic_distance,
                                              min_geodetic_distance)
from openquake.hazardlib.geo.surface.simple_fault import SimpleFaultSurface
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.hazardlib.source.characteristic import CharacteristicFaultSource
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.mfd.evenly_discretized import EvenlyDiscretizedMFD
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.calc.filters import filtered_site_to_rupture_distance
from openquake.commonlib.readinput import (get_oqparam,
                                           get_site_collection,
                                           get_job_info)

from openquake.hazardlib.imt import from_string
from openquake.commonlib import parallel
#from openquake.commonlib.calculators.classical import ClassicalCalculator
from openquake.commonlib.source import TrtModel, CompositeSourceModel
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
        centroids = np.vstack([
            centroids,
            fle[trace_idx + "/Centroids"][:].astype("float64")])
    centroids = centroids[1:, :]
    distance = min_geodetic_distance(centroids[:, 0], centroids[:, 1],
                                     sites.lons, sites.lats)
    return np.any(distance <= integration_distance)


def get_ucerf_rupture(fle, iloc, idx_set, tom, sites,
                      integration_distance, mesh_spacing=DEFAULT_MESH_SPACING,
                      trt=DEFAULT_TRT):
    """
    :param fle:
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
    #fle = h5py.File(filename, "r")
    #print idx_set["geol_idx"] + "/RuptureIndex", iloc
    ridx = fle[idx_set["geol_idx"] + "/RuptureIndex"][iloc]
    surface_set = []
    if not prefilter_ruptures(fle, ridx, idx_set, sites, integration_distance):
        return None, None
    for idx in ridx:
        # Build simple fault surface
        trace_idx = "{:s}/{:s}".format(idx_set["sec_idx"], str(idx))
        #print idx, trace_idx
        rup_plane = fle[trace_idx + "/RupturePlanes"][:].astype("float64")
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
        fle[idx_set["mag_idx"]][iloc], # Magnitude
        fle[idx_set["rake_idx"]][iloc], # Rake
        trt,
        surface_set[len(surface_set)/2].get_middle_point(), # Hypocentre
        MultiSurface(surface_set),
        CharacteristicFaultSource,
        fle[idx_set["rate_idx"]][iloc], # Rate of events
        tom)
    # Get rupture index code string
    ridx_string = "-".join([str(val) for val in ridx])
    #fle.close() # Close the UCERF File
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
    max_width = (seismogenic_layer_width
                 / math.sin(math.radians(nodal_plane.dip)))
    if rup_width > max_width:
        rup_width = max_width
        rup_length = area / rup_width
    return rup_length, rup_width


def get_rupture_surface(mag, nodal_plane, hypocenter, msr,
        rupture_aspect_ratio, upper_seismogenic_depth, lower_seismogenic_depth,
        mesh_spacing=1.0):
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
        Instance of :class:`~openquake.hazardlib.geo.surface.planar.PlanarSurface`.
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

    rup_length, rup_width = get_rupture_dimensions(mag, nodal_plane, msr,
        rupture_aspect_ratio, upper_seismogenic_depth, lower_seismogenic_depth)
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
    depths = hdd.sample(n_vals)
    nodal_planes = npd.sample(n_vals)
    for iloc, location in enumerate(locations):
        hypocentre = Point(location[0], location[1], depths[iloc][1])
        surface = get_rupture_surface(mag, nodal_planes[iloc][1],
                                      hypocentre, msr, aspect,
                                      upper_seismogenic_depth,
                                      lower_seismogenic_depth)
        rupture_probability = occurrence[iloc] * nodal_planes[iloc][0] *\
            depths[iloc][0]
        rupture_set.append(ParametricProbabilisticRupture(
            mag,
            nodal_planes[iloc][1].rake,
            trt,
            hypocentre,
            surface,
            PointSource,
            rupture_probability,
            tom))

    return rupture_set

def prefilter_background_model(fle, sites, integration_distance, msr=WC1994(),
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
    bg_locations = fle["Grid/Locations"][:].astype("float64")
    n_locations = bg_locations.shape[0]
    if not sites:
        # Apply no filtering - all sources valid
        #return np.ones(BACKGROUND_LOCS.shape[0], dtype=bool)
        return numpy.ones(n_locations, dtype=bool)
    distances = min_distance(sites.lons, sites.lats,
                             numpy.zeros_like(sites.lons),
                             bg_locations[:, 0],
                             bg_locations[:, 1],
                             np.zeros(n_locations))
    # Add buffer equal to half of length of median area from Mmax
    mmax_areas = msr.get_median_area(fle["Grid/MMax"][:], 0.0)
    mmax_lengths = numpy.sqrt(mmax_areas / aspect)
    return distances <= (0.5 * mmax_lengths + integration_distance)

def sample_background_model(fle, tom, filter_idx, min_mag, npd, hdd,
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
    bg_magnitudes = fle["Grid/Magnitudes"][:]
    # Select magnitudes above the minimum magnitudes
    mag_idx = bg_magnitudes >= min_mag
    mags = bg_magnitudes[mag_idx]
    # Filter out sites beyond integration distance
    # valid_idx = prefilter_background_model(sites, integration_distance, msr)
    #print np.where(valid_idx)[0], np.where(mag_idx)[0]
    rates = fle["Grid/RateArray"][filter_idx, :]
    rates = rates[:, mag_idx]
    valid_locs = fle["Grid/Locations"][filter_idx, :]
    # Sample remaining rates
    sampler = tom.sample_number_of_occurrences(rates)
    background_ruptures = []
    background_n_occ = []
    for iloc, mag in enumerate(mags):
        rate_idx = numpy.where(sampler[:, iloc])[0]
        rate_cnt = sampler[rate_idx, iloc]
        occurrence = rates[rate_idx, iloc]
        locations = valid_locs[rate_idx, :]
        rupture_set = generate_background_ruptures(tom, locations, occurrence,
            mag, npd, hdd, upper_seismogenic_depth,
            lower_seismogenic_depth, msr, aspect, trt)
        background_ruptures.extend(rupture_set)
        background_n_occ.extend(rate_cnt.tolist())
    return background_ruptures, background_n_occ


class UCERFSESControl(object):
    """

    """
    def __init__(self, source_file, id, investigation_time, min_mag,
                 npd=NPD, hdd=HDD, aspect=1.5,
                 upper_seismogenic_depth=0.0, lower_seismogenic_depth=15.,
                 msr=WC1994(), mesh_spacing=1.0, trt="Active Shallow Crust",
                 integration_distance=1000):
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
        #assert branch_id in VALID_BRANCHES
        assert os.path.exists(source_file)
        self.source_file = source_file
        self.source_id = id
#        self.id = branch_id
#        self.idxset = build_idx_set(self.id)
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
        self.integration_distance = integration_distance
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
        fle = h5py.File(self.source_file)
        self.background_idx = prefilter_background_model(
            fle,
            self.sites,
            integration_distance,
            self.msr,
            self.aspect)
        fle.close()

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
        fle = h5py.File(self.source_file, "r+")
        rates = fle[idxset["rate_idx"]][:]
        occurrences = self.tom.sample_number_of_occurrences(rates)
        indices = numpy.where(occurrences)[0]
        print indices
        # Get ruptures from the indices
        rupture_set = []
        rupture_occ = []
        for idx, n_occ in zip(indices, occurrences[indices]):
            ucerf_rup = get_ucerf_rupture(fle, idx, idxset, self.tom,
                                          self.sites,
                                          self.integration_distance,
                                          self.mesh_spacing,
                                          self.tectonic_region_type)[0]
            
            if ucerf_rup:
                rupture_set.append(ucerf_rup)
                rupture_occ.append(n_occ)

        # Sample Background sources
        background_ruptures, background_n_occ = sample_background_model(
            fle,
            self.tom,
            self.background_idx,
            self.min_mag,
            self.npd, self.hdd, 
            self.usd, self.lsd,
            self.msr, self.aspect,
            self.tectonic_region_type)
        rupture_set.extend(background_ruptures)
        rupture_occ.extend(background_n_occ)
        fle.close()
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


def get_geom(surface, is_from_fault_source, is_multi_surface):
    """
    The following fields can be interpreted different ways,
    depending on the value of `is_from_fault_source`. If
    `is_from_fault_source` is True, each of these fields should
    contain a 2D numpy array (all of the same shape). Each triple
    of (lon, lat, depth) for a given index represents the node of
    a rectangular mesh. If `is_from_fault_source` is False, each
    of these fields should contain a sequence (tuple, list, or
    numpy array, for example) of 4 values. In order, the triples
    of (lon, lat, depth) represent top left, top right, bottom
    left, and bottom right corners of the the rupture's planar
    surface. Update: There is now a third case. If the rupture
    originated from a characteristic fault source with a
    multi-planar-surface geometry, `lons`, `lats`, and `depths`
    will contain one or more sets of 4 points, similar to how
    planar surface geometry is stored (see above).

    :param rupture: an instance of :class:`openquake.hazardlib.source.rupture.BaseProbabilisticRupture`
    :param is_from_fault_source: a boolean
    :param is_multi_surface: a boolean
    """
    if is_from_fault_source:
        # for simple and complex fault sources,
        # rupture surface geometry is represented by a mesh
        surf_mesh = surface.get_mesh()
        lons = surf_mesh.lons
        lats = surf_mesh.lats
        depths = surf_mesh.depths
    else:
        if is_multi_surface:
            # `list` of
            # openquake.hazardlib.geo.surface.planar.PlanarSurface
            # objects:
            surfaces = surface.surfaces

            # lons, lats, and depths are arrays with len == 4*N,
            # where N is the number of surfaces in the
            # multisurface for each `corner_*`, the ordering is:
            #   - top left
            #   - top right
            #   - bottom left
            #   - bottom right
            lons = numpy.concatenate([x.corner_lons for x in surfaces])
            lats = numpy.concatenate([x.corner_lats for x in surfaces])
            depths = numpy.concatenate([x.corner_depths for x in surfaces])
        else:
            # For area or point source,
            # rupture geometry is represented by a planar surface,
            # defined by 3D corner points
            lons = numpy.zeros((4))
            lats = numpy.zeros((4))
            depths = numpy.zeros((4))

            # NOTE: It is important to maintain the order of these
            # corner points. TODO: check the ordering
            for i, corner in enumerate((surface.top_left,
                                        surface.top_right,
                                        surface.bottom_left,
                                        surface.bottom_right)):
                lons[i] = corner.longitude
                lats[i] = corner.latitude
                depths[i] = corner.depth
    return lons, lats, depths


class EBRupture(object):
    """
    An event based rupture. It is a wrapper over a hazardlib rupture
    object, containing an array of site indices affected by the rupture,
    as well as the tags of the corresponding seismic events.
    """
    def __init__(self, rupture, indices, etags, trt_id, serial):
        self.rupture = rupture
        self.indices = indices
        self.etags = numpy.array(etags)
        self.trt_id = trt_id
        self.serial = serial

    @property
    def multiplicity(self):
        """
        How many times the underlying rupture occurs.
        """
        return len(self.etags)

    def export(self, mesh):
        """
        Yield :class:`openquake.commonlib.util.Rupture` objects, with all the
        attributes set, suitable for export in XML format.
        """
        rupture = self.rupture
        for etag in self.etags:
            new = Rupture(etag, self.indices)
            new.mesh = mesh[self.indices]
            new.etag = etag
            new.rupture = new
            new.is_from_fault_source = iffs = isinstance(
                rupture.surface, (geo.ComplexFaultSurface,
                                  geo.SimpleFaultSurface))
            new.is_multi_surface = ims = isinstance(
                rupture.surface, geo.MultiSurface)
            new.lons, new.lats, new.depths = get_geom(
                rupture.surface, iffs, ims)
            new.surface = rupture.surface
            new.strike = rupture.surface.get_strike()
            new.dip = rupture.surface.get_dip()
            new.rake = rupture.rake
            new.hypocenter = rupture.hypocenter
            new.tectonic_region_type = rupture.tectonic_region_type
            new.magnitude = new.mag = rupture.mag
            new.top_left_corner = None if iffs or ims else (
                new.lons[0], new.lats[0], new.depths[0])
            new.top_right_corner = None if iffs or ims else (
                new.lons[1], new.lats[1], new.depths[1])
            new.bottom_left_corner = None if iffs or ims else (
                new.lons[2], new.lats[2], new.depths[2])
            new.bottom_right_corner = None if iffs or ims else (
                new.lons[3], new.lats[3], new.depths[3])
            yield new

    def __lt__(self, other):
        return self.serial < other.serial

    def __repr__(self):
        return '<%s #%d, trt_id=%d>' % (self.__class__.__name__,
                                        self.serial, self.trt_id)


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

#@parallel.litetask
def compute_ruptures(branch_info, source, sitecol, oqparam):
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
    #trt_model_id = source.trt
    #oq = monitor.oqparam
    integration_distance = oqparam.maximum_distance["default"]
    ltbrid, branch_id, _ = branch_info
    ses_ruptures = []

    #col_ids = info.col_ids_by_trt_id[trt_model_id]
    serial = 1
    trt_model_id = 1
    
    # Pre-filter
    source.update_background_site_filter(sitecol,
                                         integration_distance)
    #for col_in in col_ids:
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
            
            #seed = source.rnd.randint(0, MAX_INT)

            if len(etags):
                ses_ruptures.append(
                    EBRupture(rup, indices, etags, trt_model_id, serial))
                serial += 1
    res = AccumDict({ltbrid: ses_ruptures})
    #res.calc_times = calc_times
    #res.rup_data = numpy.array(rup_data, rup_data_dt)
    res.trt = source.tectonic_region_type
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
        parser = SourceModelParser(converter)
        self.source = parser.parse_sources(
            self.oqparam.inputs["source_file"])[0]
        self.read_risk_data()

    def execute(self):
        """
        Run the ucerf event based calculation
        """
        id_set = [(key, self.smlt.branches[key].value,
                  self.smlt.branches[key].weight)
                  for key in self.smlt.branches.keys()]
        ruptures_by_branch_id = parallel.apply_reduce(
            compute_ruptures,
            (id_set, self.source, self.sitecol, self.oqparam)
        )
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
        and save the rup_data
        """
        acc += val
        if len(val.rup_data):
            try:
                dset = self.rup_data[val.trt]
            except KeyError:
                dset = self.rup_data[val.trt] = self.datastore.create_dset(
                    'rup_data/' + val.trt, val.rup_data.dtype)
            dset.extend(val.rup_data)

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
            nc = self.rlzs_assoc.csm_info.num_collections
            sescollection = [[] for trt_id in range(nc)]
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
        for dset in self.rup_data.values():
            numsites = dset.dset['numsites']
            multiplicity = dset.dset['multiplicity']
            spr = numpy.average(numsites, weights=multiplicity)
            mul = numpy.average(multiplicity, weights=numsites)
            self.datastore.set_attrs(dset.name, sites_per_rupture=spr,
                                     multiplicity=mul)
        self.datastore.set_nbytes('rup_data')


# ######################## GMF calculator ############################ #

GmfaSidsEtags = collections.namedtuple('GmfaSidsEtags', 'gmfa sids etags')


def make_gmfs(eb_ruptures, sitecol, imts, gsims,
              trunc_level, correl_model, monitor=Monitor()):
    """
    :param eb_ruptures: a list of EBRuptures
    :param sitecol: a SiteCollection instance
    :param imts: an ordered list of intensity measure type strings
    :param gsims: an order list of GSIM instance
    :param trunc_level: truncation level
    :param correl_model: correlation model instance
    :param monitor: a monitor instance
    :returns: a dictionary serial -> GmfaSidsEtags
    """
    dic = {}  # serial -> GmfaSidsEtags
    ctx_mon = monitor('make contexts')
    gmf_mon = monitor('compute poes')
    sites = sitecol.complete
    for ebr in eb_ruptures:
        with ctx_mon:
            r_sites = (sitecol if ebr.indices is None else
                       site.FilteredSiteCollection(ebr.indices, sites))
            computer = calc.gmf.GmfComputer(
                ebr.rupture, r_sites, imts, gsims, trunc_level, correl_model)
        with gmf_mon:
            gmfa = computer.calcgmfs(ebr.multiplicity, ebr.rupture.seed)
            dic[ebr.serial] = GmfaSidsEtags(gmfa, r_sites.indices, ebr.etags)
    return dic


@parallel.litetask
def compute_gmfs_and_curves(eb_ruptures, sitecol, rlzs_assoc, monitor):
    """
    :param eb_ruptures:
        a list of blocks of EBRuptures of the same SESCollection
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param rlzs_assoc:
        a RlzsAssoc instance
    :param monitor:
        a Monitor instance
    :returns:
        a dictionary (trt_model_id, gsim) -> haz_curves and/or
        (trt_model_id, col_id) -> gmfs
   """
    oq = monitor.oqparam
    # NB: by construction each block is a non-empty list with
    # ruptures of the same col_id and therefore trt_model_id
    trt_id = eb_ruptures[0].trt_id
    gsims = rlzs_assoc.gsims_by_trt_id[trt_id]
    trunc_level = oq.truncation_level
    correl_model = readinput.get_correl_model(oq)
    tot_sites = len(sitecol.complete)
    gmfa_sids_etags = make_gmfs(
        eb_ruptures, sitecol, oq.imtls, gsims, trunc_level, correl_model,
        monitor)
    result = {trt_id: gmfa_sids_etags if oq.ground_motion_fields else None}
    if oq.hazard_curves_from_gmfs:
        with monitor('bulding hazard curves', measuremem=False):
            duration = oq.investigation_time * oq.ses_per_logic_tree_path * (
                oq.number_of_logic_tree_samples or 1)

            # collect the gmvs by site
            gmvs_by_sid = collections.defaultdict(list)
            for serial in gmfa_sids_etags:
                gst = gmfa_sids_etags[serial]
                for sid, gmvs in zip(gst.sids, gst.gmfa.T):
                    gmvs_by_sid[sid].extend(gmvs)

            # build the hazard curves for each GSIM
            for gsim in gsims:
                gs = str(gsim)
                result[trt_id, gs] = to_haz_curves(
                    tot_sites, gmvs_by_sid, gs, oq.imtls,
                    oq.investigation_time, duration)
    return result


def to_haz_curves(num_sites, gmvs_by_sid, gs, imtls,
                  investigation_time, duration):
    """
    :param num_sites: length of the full site collection
    :param gmvs_by_sid: dictionary site_id -> gmvs
    :param gs: GSIM string
    :param imtls: ordered dictionary {IMT: intensity measure levels}
    :param investigation_time: investigation time
    :param duration: investigation_time * number of Stochastic Event Sets
    """
    curves = zero_curves(num_sites, imtls)
    for imt in imtls:
        curves[imt] = numpy.array([
            gmvs_to_haz_curve(
                [gmv[gs][imt] for gmv in gmvs_by_sid[sid]],
                imtls[imt], investigation_time, duration)
            for sid in range(num_sites)])
    return curves


@base.calculators.add('event_based')
class EventBasedCalculator(ClassicalCalculator):
    """
    Event based PSHA calculator generating the ground motion fields and
    the hazard curves from the ruptures, depending on the configuration
    parameters.
    """
    pre_calculator = 'event_based_rupture'
    core_task = compute_gmfs_and_curves
    is_stochastic = True

    def pre_execute(self):
        """
        Read the precomputed ruptures (or compute them on the fly) and
        prepare some empty files in the export directory to store the gmfs
        (if any). If there were pre-existing files, they will be erased.
        """
        super(EventBasedCalculator, self).pre_execute()
        self.sesruptures = []
        for trt_id in range(self.rlzs_assoc.csm_info.num_collections):
            sescol = self.datastore['sescollection/trt=%02d' % trt_id]
            self.sesruptures.extend(sescol)

    def combine_curves_and_save_gmfs(self, acc, res):
        """
        Combine the hazard curves (if any) and save the gmfs (if any)
        sequentially; notice that the gmfs may come from
        different tasks in any order.

        :param acc: an accumulator for the hazard curves
        :param res: a dictionary trt_id, gsim -> gmf_array or curves_by_imt
        :returns: a new accumulator
        """
        sav_mon = self.monitor('saving gmfs')
        agg_mon = self.monitor('aggregating hcurves')
        save_gmfs = self.oqparam.ground_motion_fields
        for trt_id in res:
            if isinstance(trt_id, int) and save_gmfs:
                with sav_mon:
                    gmfa_sids_etags = res[trt_id]
                    for serial in sorted(gmfa_sids_etags):
                        gst = gmfa_sids_etags[serial]
                        self.datastore['gmf_data/%s' % serial] = gst.gmfa
                        self.datastore['sid_data/%s' % serial] = gst.sids
                        self.datastore.set_attrs('gmf_data/%s' % serial,
                                                 trt_id=trt_id,
                                                 etags=gst.etags)
                    self.datastore.hdf5.flush()
            elif isinstance(trt_id, tuple):  # aggregate hcurves
                with agg_mon:
                    self.agg_dicts(acc, {trt_id: res[trt_id]})
        sav_mon.flush()
        agg_mon.flush()
        return acc

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the ruptures according to their weight and
        tectonic region type.
        """
        oq = self.oqparam
        if not oq.hazard_curves_from_gmfs and not oq.ground_motion_fields:
            return
        monitor = self.monitor(self.core_task.__name__)
        monitor.oqparam = oq
        zc = zero_curves(len(self.sitecol.complete), self.oqparam.imtls)
        zerodict = AccumDict((key, zc) for key in self.rlzs_assoc)
        curves_by_trt_gsim = parallel.apply_reduce(
            self.core_task.__func__,
            (self.sesruptures, self.sitecol, self.rlzs_assoc, monitor),
            concurrent_tasks=self.oqparam.concurrent_tasks,
            acc=zerodict, agg=self.combine_curves_and_save_gmfs,
            key=operator.attrgetter('trt_id'),
            weight=operator.attrgetter('multiplicity'))
        if oq.ground_motion_fields:
            self.datastore.set_nbytes('gmf_data')
            self.datastore.set_nbytes('sid_data')
        return curves_by_trt_gsim

    def post_execute(self, result):
        """
        :param result:
            a dictionary (trt_model_id, gsim) -> haz_curves or an empty
            dictionary if hazard_curves_from_gmfs is false
        """
        oq = self.oqparam
        if not oq.hazard_curves_from_gmfs and not oq.ground_motion_fields:
            return
        if oq.hazard_curves_from_gmfs:
            ClassicalCalculator.post_execute.__func__(self, result)
        if oq.compare_with_classical:  # compute classical curves
            export_dir = os.path.join(oq.export_dir, 'cl')
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            oq.export_dir = export_dir
            # use a different datastore
            self.cl = ClassicalCalculator(oq, self.monitor)
            self.cl.datastore.parent = self.datastore
            # TODO: perhaps it is possible to avoid reprocessing the source
            # model, however usually this is quite fast and do not dominate
            # the computation
            result = self.cl.run()
            for imt in self.mean_curves.dtype.fields:
                rdiff, index = max_rel_diff_index(
                    self.cl.mean_curves[imt], self.mean_curves[imt])
                logging.warn('Relative difference with the classical '
                             'mean curves for IMT=%s: %d%% at site index %d',
                             imt, rdiff * 100, index)















#@parallel.litetask
#def compute_ruptures(sources, sitecol, siteidx, rlzs_assoc, monitor):
#    """
#    :param sources:
#        List of commonlib.source.Source tuples
#    :param sitecol:
#        a :class:`openquake.hazardlib.site.SiteCollection` instance
#    :param siteidx:
#        always equal to 0
#    :param rlzs_assoc:
#        a :class:`openquake.commonlib.source.RlzsAssoc` instance
#    :param monitor:
#        monitor instance
#    :returns:
#        a dictionary trt_model_id -> [Rupture instances]
#    """
#    assert siteidx == 0, (
#        'siteidx can be nonzero only for the classical_tiling calculations: '
#        'tiling with the EventBasedRuptureCalculator is an error')
#    # NB: by construction each block is a non-empty list with
#    # sources of the same trt_model_id
#    trt_model_id = sources[0].trt_model_id
#    oq = monitor.oqparam
#    trt = sources[0].tectonic_region_type
#    try:
#        max_dist = oq.maximum_distance[trt]
#    except KeyError:
#        max_dist = oq.maximum_distance['default']
#    totsites = len(sitecol)
#    cmaker = ContextMaker(rlzs_assoc.gsims_by_trt_id[trt_model_id])
#    params = cmaker.REQUIRES_RUPTURE_PARAMETERS
#    rup_data_dt = numpy.dtype(
#        [('rupserial', U32), ('multiplicity', U16), ('numsites', U32)] + [
#            (param, F32) for param in params])
#
#    eb_ruptures = []
#    rup_data = []
#    calc_times = []
#
#    # Compute and save stochastic event sets
#    for src in sources:
#        t0 = time.time()
#        s_sites = src.filter_sites_by_distance_to_source(max_dist, sitecol)
#        if s_sites is None:
#            continue
#
#        num_occ_by_rup = sample_ruptures(
#            src, oq.ses_per_logic_tree_path, rlzs_assoc.csm_info)
#        # NB: the number of occurrences is very low, << 1, so it is
#        # more efficient to filter only the ruptures that occur, i.e.
#        # to call sample_ruptures *before* the filtering
#        for ebr in build_eb_ruptures(
#                src, num_occ_by_rup, s_sites, max_dist, sitecol,
#                oq.random_seed):
#            nsites = totsites if ebr.indices is None else len(ebr.indices)
#            rc = cmaker.make_rupture_context(ebr.rupture)
#            ruptparams = tuple(getattr(rc, param) for param in params)
#            rup_data.append((ebr.serial, len(ebr.etags), nsites) + ruptparams)
#            eb_ruptures.append(ebr)
#        dt = time.time() - t0
#        calc_times.append((src.id, dt))
#    res = AccumDict({trt_model_id: eb_ruptures})
#    res.calc_times = calc_times
#    res.rup_data = numpy.array(rup_data, rup_data_dt)
#    res.trt = trt
#    return res


#def sample_ruptures(src, num_ses, info):
#    """
#    Sample the ruptures contained in the given source.
#
#    :param src: a hazardlib source object
#    :param num_ses: the number of Stochastic Event Sets to generate
#    :param info: a :class:`openquake.commonlib.source.CompositionInfo` instance
#    :returns: a dictionary of dictionaries rupture ->
#              {(col_id, ses_id): num_occurrences}
#    """
#    col_ids = info.col_ids_by_trt_id[src.trt_model_id]
#    # the dictionary `num_occ_by_rup` contains a dictionary
#    # (col_id, ses_id) -> num_occurrences
#    # for each occurring rupture
#    num_occ_by_rup = collections.defaultdict(AccumDict)
#    # generating ruptures for the given source
#    for rup_no, rup in enumerate(src.iter_ruptures()):
#        rup.seed = seed = src.serial[rup_no] + info.seed
#        numpy.random.seed(seed)
#        for col_id in col_ids:
#            for ses_idx in range(1, num_ses + 1):
#                num_occurrences = rup.sample_number_of_occurrences()
#                if num_occurrences:
#                    num_occ_by_rup[rup] += {
#                        (col_id, ses_idx): num_occurrences}
#        rup.rup_no = rup_no + 1
#    return num_occ_by_rup
#
#
#def build_eb_ruptures(
#        src, num_occ_by_rup, s_sites, maximum_distance, sitecol, random_seed):
#    """
#    Filter the ruptures stored in the dictionary num_occ_by_rup and
#    yield pairs (rupture, <list of associated EBRuptures>)
#    """
#    totsites = len(sitecol)
#    for rup in sorted(num_occ_by_rup, key=operator.attrgetter('rup_no')):
#        # filtering ruptures
#        r_sites = filter_sites_by_distance_to_rupture(
#            rup, maximum_distance, s_sites)
#        if r_sites is None:
#            # ignore ruptures which are far away
#            del num_occ_by_rup[rup]  # save memory
#            continue
#        if len(r_sites) < totsites:
#            indices = r_sites.indices
#        else:
#            indices = None  # None means that nothing was filtered
#
#        # creating EBRuptures
#        serial = rup.seed - random_seed + 1
#        etags = []
#        for (col_idx, ses_idx), num_occ in sorted(
#                num_occ_by_rup[rup].items()):
#            for occ_no in range(1, num_occ + 1):
#                etag = 'col=%02d~ses=%04d~src=%s~rup=%d-%02d' % (
#                    col_idx, ses_idx, src.source_id, serial, occ_no)
#                etags.append(etag)
#        if etags:
#            yield EBRupture(rup, indices, etags, src.trt_model_id, serial)
