# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2019 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import os
import copy
import math
from datetime import datetime
import numpy
import h5py
from openquake.baselib.general import random_filter
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.source.base import BaseSeismicSource
from openquake.hazardlib.geo.geodetic import min_geodetic_distance
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.mfd import EvenlyDiscretizedMFD
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib import valid
from openquake.hazardlib.sourceconverter import SourceConverter

DEFAULT_TRT = "Active Shallow Crust"
RUPTURES_PER_BLOCK = 200  # decided by MS
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


def convert_UCERFSource(self, node):
    """
    Converts the Ucerf Source node into an SES Control object
    """
    dirname = os.path.dirname(self.fname)  # where the source_model_file is
    source_file = os.path.join(dirname, node["filename"])
    if "startDate" in node.attrib and "investigationTime" in node.attrib:
        # Is a time-dependent model - even if rates were originally
        # poissonian
        # Verify that the source time span is the same as the TOM time span
        inv_time = float(node["investigationTime"])
        if inv_time != self.investigation_time:
            raise ValueError("Source investigation time (%s) is not "
                             "equal to configuration investigation time "
                             "(%s)" % (inv_time, self.investigation_time))
        start_date = datetime.strptime(node["startDate"], "%d/%m/%Y")
    else:
        start_date = None
    return UCERFSource(
        source_file,
        self.investigation_time,
        start_date,
        float(node["minMag"]),
        npd=self.convert_npdist(node),
        hdd=self.convert_hpdist(node),
        aspect=~node.ruptAspectRatio,
        upper_seismogenic_depth=~node.pointGeometry.upperSeismoDepth,
        lower_seismogenic_depth=~node.pointGeometry.lowerSeismoDepth,
        msr=valid.SCALEREL[~node.magScaleRel](),
        mesh_spacing=self.rupture_mesh_spacing,
        trt=node["tectonicRegion"])


SourceConverter.convert_UCERFSource = convert_UCERFSource


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


class UcerfFilter(SourceFilter):
    """
    Filter for UCERF sources, both background and faults.
    """
    def filter(self, srcs):
        for src in srcs:
            if hasattr(src, 'start'):  # fault sources
                src.src_filter = self  # hack: needed for .iter_ruptures
                ridx = set()
                for idx in range(src.start, src.stop):
                    ridx.update(src.get_ridx(idx))
                mag = src.mags[src.start:src.stop].max()
                src.indices = self.get_indices(src, ridx, mag)
                if len(src.indices):
                    yield src
            else:  # background sources
                yield from super().filter([src])

    def get_indices(self, src, ridx, mag):
        """
        :param src: an UCERF source
        :param ridx: a set of rupture indices
        :param mag: magnitude to use to compute the integration distance
        :returns: array with the IDs of the sites close to the ruptures
        """
        centroids = src.get_centroids(ridx)
        mindistance = min_geodetic_distance(
            (centroids[:, 0], centroids[:, 1]), self.sitecol.xyz)
        idist = self.integration_distance(DEFAULT_TRT, mag)
        indices, = (mindistance <= idist).nonzero()
        return indices


class UCERFSource(BaseSeismicSource):
    """
    :param source_file:
        Path to an existing HDF5 file containing the UCERF model
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
    code = b'U'
    MODIFICATIONS = set()
    tectonic_region_type = DEFAULT_TRT
    RUPTURE_WEIGHT = 1  # not very heavy

    def __init__(
            self, source_file, investigation_time, start_date, min_mag,
            npd=NPD, hdd=HDD, aspect=1.5, upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=15.0, msr=WC1994(), mesh_spacing=1.0,
            trt="Active Shallow Crust", integration_distance=1000):
        assert os.path.exists(source_file), source_file
        self.source_file = source_file
        self.source_id = None  # unset until .new is called
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
        self.stop = 0
        self.start = -1
        self.orig = None  # set by .new()

    @property
    def num_ruptures(self):
        return self.stop - self.start

    @num_ruptures.setter
    def num_ruptures(self, value):  # hack to make the sourceconverter happy
        pass

    @property
    def mags(self):
        # read from FM0_0/MEANFS/MEANMSR/Magnitude
        if hasattr(self.orig, '_mags'):
            return self.orig._mags
        with h5py.File(self.source_file, "r") as hdf5:
            self.orig._mags = hdf5[self.idx_set["mag"]].value
            return self.orig._mags

    @property
    def rate(self):
        # read from FM0_0/MEANFS/MEANMSR/Rates/MeanRates
        if hasattr(self.orig, '_rate'):
            return self.orig._rate
        with h5py.File(self.source_file, "r") as hdf5:
            self.orig._rate = hdf5[self.idx_set["rate"]].value
            return self.orig._rate

    @property
    def rake(self):
        # read from FM0_0/MEANFS/Rake
        if hasattr(self.orig, '_rake'):
            return self.orig._rake
        with h5py.File(self.source_file, "r") as hdf5:
            self.orig._rake = hdf5[self.idx_set["rake"]].value
            return self.orig._rake

    def count_ruptures(self):
        """
        The length of the rupture array if the branch_id is set, else 0
        """
        return self.num_ruptures

    def new(self, grp_id, branch_id):
        """
        :param grp_id: ordinal of the source group
        :param branch_name: name of the UCERF branch
        :param branch_id: string associated to the branch
        :returns: a new UCERFSource associated to the branch_id
        """
        new = copy.copy(self)
        new.orig = new
        new.src_group_id = grp_id
        new.source_id = branch_id
        new.idx_set = build_idx_set(branch_id, self.start_date)
        with h5py.File(self.source_file, "r") as hdf5:
            new.start = 0
            new.stop = len(hdf5[new.idx_set["mag"]])
        return new

    def get_min_max_mag(self):
        """
        Called when updating the SourceGroup
        """
        return self.min_mag, 10

    def _get_tom(self):
        """
        Returns the temporal occurence model as a Poisson TOM
        """
        return PoissonTOM(self.inv_time)

    def get_ridx(self, iloc):
        """List of rupture indices for the given iloc"""
        with h5py.File(self.source_file, "r") as hdf5:
            return hdf5[self.idx_set["geol"] + "/RuptureIndex"][iloc]

    def get_centroids(self, ridx):
        """
        :returns: array of centroids for the given rupture index
        """
        centroids = []
        with h5py.File(self.source_file, "r") as hdf5:
            for idx in ridx:
                trace = "{:s}/{:s}".format(self.idx_set["sec"], str(idx))
                centroids.append(hdf5[trace + "/Centroids"].value)
        return numpy.concatenate(centroids)

    def gen_trace_planes(self, ridx):
        """
        :yields: trace and rupture planes for the given rupture index
        """
        with h5py.File(self.source_file, "r") as hdf5:
            for idx in ridx:
                trace = "{:s}/{:s}".format(self.idx_set["sec"], str(idx))
                plane = hdf5[trace + "/RupturePlanes"][:].astype("float64")
                yield trace, plane

    def get_background_sids(self, src_filter):
        """
        We can apply the filtering of the background sites as a pre-processing
        step - this is done here rather than in the sampling of the ruptures
        themselves
        """
        branch_key = self.idx_set["grid_key"]
        idist = src_filter.integration_distance(DEFAULT_TRT)
        with h5py.File(self.source_file, 'r') as hdf5:
            bg_locations = hdf5["Grid/Locations"].value
            distances = min_geodetic_distance(
                src_filter.sitecol.xyz,
                (bg_locations[:, 0], bg_locations[:, 1]))
            # Add buffer equal to half of length of median area from Mmax
            mmax_areas = self.msr.get_median_area(
                hdf5["/".join(["Grid", branch_key, "MMax"])].value, 0.0)
            # for instance hdf5['Grid/FM0_0_MEANFS_MEANMSR/MMax']
            mmax_lengths = numpy.sqrt(mmax_areas / self.aspect)
            ok = distances <= (0.5 * mmax_lengths + idist)
            # get list of indices from array of booleans
            return numpy.where(ok)[0].tolist()

    def get_ucerf_rupture(self, iloc, src_filter):
        """
        :param iloc:
            Location of the rupture plane in the hdf5 file
        :param src_filter:
            Sites for consideration and maximum distance
        """
        trt = self.tectonic_region_type
        ridx = self.get_ridx(iloc)
        mag = self.orig.mags[iloc]
        surface_set = []
        indices = src_filter.get_indices(self, ridx, mag)
        if len(indices) == 0:
            return None
        for trace, plane in self.gen_trace_planes(ridx):
            # build simple fault surface
            for jloc in range(0, plane.shape[2]):
                top_left = Point(
                    plane[0, 0, jloc], plane[0, 1, jloc], plane[0, 2, jloc])
                top_right = Point(
                    plane[1, 0, jloc], plane[1, 1, jloc], plane[1, 2, jloc])
                bottom_right = Point(
                    plane[2, 0, jloc], plane[2, 1, jloc], plane[2, 2, jloc])
                bottom_left = Point(
                    plane[3, 0, jloc], plane[3, 1, jloc], plane[3, 2, jloc])
                try:
                    surface_set.append(
                        ImperfectPlanarSurface.from_corner_points(
                            top_left, top_right, bottom_right, bottom_left))
                except ValueError as err:
                    raise ValueError(err, trace, top_left, top_right,
                                     bottom_right, bottom_left)

        rupture = ParametricProbabilisticRupture(
            mag, self.orig.rake[iloc], trt,
            surface_set[len(surface_set) // 2].get_middle_point(),
            MultiSurface(surface_set), self.orig.rate[iloc], self.tom)

        return rupture

    def iter_ruptures(self):
        """
        Yield ruptures for the current set of indices
        """
        assert self.orig, '%s is not fully initialized' % self
        for ridx in range(self.start, self.stop):
            if self.orig.rate[ridx]:  # ruptures may have have zero rate
                rup = self.get_ucerf_rupture(ridx, self.src_filter)
                if rup:
                    yield rup

    def __iter__(self):
        assert self.orig, '%s is not fully initialized' % self
        start = self.start
        stop = self.stop
        while stop > start:
            new = copy.copy(self)
            new.id = self.id
            new.orig = self.orig
            new.start = start
            new.stop = min(start + RUPTURES_PER_BLOCK, stop)
            start += RUPTURES_PER_BLOCK
            yield new

    def __repr__(self):
        return '<%s %s[%d:%d]>' % (self.__class__.__name__, self.source_id,
                                   self.start, self.stop)

    def get_background_sources(self, src_filter, sample_factor=None):
        """
        Turn the background model of a given branch into a set of point sources

        :param src_filter:
            SourceFilter instance
        :param sample_factor:
            Used to reduce the sources if OQ_SAMPLE_SOURCES is set
        """
        background_sids = self.get_background_sids(src_filter)
        if sample_factor is not None:  # hack for use in the mosaic
            background_sids = random_filter(
                background_sids, sample_factor, seed=42)
        with h5py.File(self.source_file, "r") as hdf5:
            grid_loc = "/".join(["Grid", self.idx_set["grid_key"]])
            # for instance Grid/FM0_0_MEANFS_MEANMSR_MeanRates
            mags = hdf5[grid_loc + "/Magnitude"].value
            mmax = hdf5[grid_loc + "/MMax"][background_sids]
            rates = hdf5[grid_loc + "/RateArray"][background_sids, :]
            locations = hdf5["Grid/Locations"][background_sids, :]
            sources = []
            for i, bg_idx in enumerate(background_sids):
                src_id = "_".join([self.idx_set["grid_key"], str(bg_idx)])
                src_name = "|".join([self.idx_set["total_key"], str(bg_idx)])
                mag_idx = (self.min_mag <= mags) & (mags < mmax[i])
                src_mags = mags[mag_idx]
                src_mfd = EvenlyDiscretizedMFD(
                    src_mags[0],
                    src_mags[1] - src_mags[0],
                    rates[i, mag_idx].tolist())
                ps = PointSource(
                    src_id, src_name, self.tectonic_region_type, src_mfd,
                    self.mesh_spacing, self.msr, self.aspect, self.tom,
                    self.usd, self.lsd,
                    Point(locations[i, 0], locations[i, 1]),
                    self.npd, self.hdd)
                ps.id = self.id
                ps.src_group_id = self.src_group_id
                ps.num_ruptures = ps.count_ruptures()
                sources.append(ps)
        return sources

    def get_one_rupture(self):
        raise ValueError('Unsupported option')


def build_idx_set(branch_id, start_date):
    """
    Builds a dictionary of keys based on the branch code
    """
    code_set = branch_id.split("/")
    code_set.insert(3, "Rates")
    idx_set = {
        "sec": "/".join([code_set[0], code_set[1], "Sections"]),
        "mag": "/".join([code_set[0], code_set[1], code_set[2], "Magnitude"])}
    idx_set["rate"] = "/".join(code_set)
    idx_set["rake"] = "/".join([code_set[0], code_set[1], "Rake"])
    idx_set["msr"] = "-".join(code_set[:3])
    idx_set["geol"] = code_set[0]
    if start_date:  # time-dependent source
        idx_set["grid_key"] = "_".join(
            branch_id.replace("/", "_").split("_")[:-1])
    else:  # time-independent source
        idx_set["grid_key"] = branch_id.replace("/", "_")
    idx_set["total_key"] = branch_id.replace("/", "|")
    return idx_set


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
            azimuth=(azimuth_up if vshift < 0 else azimuth_down))

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
        math.atan((rup_proj_width / 2.) / (rup_length / 2.)))
    hor_dist = math.sqrt(
        (rup_length / 2.) ** 2 + (rup_proj_width / 2.) ** 2)
    left_top = rupture_center.point_at(
        horizontal_distance=hor_dist,
        vertical_increment=-rup_proj_height / 2,
        azimuth=(nodal_plane.strike + 180 + theta) % 360)
    right_top = rupture_center.point_at(
        horizontal_distance=hor_dist,
        vertical_increment=-rup_proj_height / 2,
        azimuth=(nodal_plane.strike - theta) % 360)
    left_bottom = rupture_center.point_at(
        horizontal_distance=hor_dist,
        vertical_increment=rup_proj_height / 2,
        azimuth=(nodal_plane.strike + 180 - theta) % 360)
    right_bottom = rupture_center.point_at(
        horizontal_distance=hor_dist,
        vertical_increment=rup_proj_height / 2,
        azimuth=(nodal_plane.strike + theta) % 360)
    return PlanarSurface(nodal_plane.strike, nodal_plane.dip,
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
            rupture_probability, tom))
    return ruptures
