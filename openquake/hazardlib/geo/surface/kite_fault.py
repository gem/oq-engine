# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020 GEM Foundation
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

"""
Module :mod:`openquake.hazardlib.geo.surface.kite_fault` defines
:class:`KiteFaultSurface`.
"""
import numpy as np

from openquake.baselib.node import Node
from openquake.hazardlib.geo.geodetic import distance, azimuth
from openquake.hazardlib.geo.surface.base import BaseSurface
from openquake.hazardlib.geo.mesh import Mesh, RectangularMesh
from openquake.hazardlib.geo import utils as geo_utils
from openquake.hazardlib.geo.point import Point


class KiteFaultSurface(BaseSurface):
    """
    """
    def __init__(self, mesh):
        self.mesh = mesh
        assert 1 not in self.mesh.shape, (
            "Mesh must have at least 2 nodes along both length and width.")
        self.strike = self.dip = None

    def get_dip(self):
        """
        Return the fault dip as the average dip over the fault surface mesh.

        The average dip is defined as the weighted mean inclination of top
        row of mesh cells. See
        :meth:`openquake.hazardlib.geo.mesh.RectangularMesh.get_mean_inclination_and_azimuth`

        :returns:
            The average dip, in decimal degrees.
        """
        pass

    def get_strike(self):
        """
        Return the fault strike as the average strike along the fault trace.

        The average strike is defined as the weighted mean azimuth of top
        row of mesh cells. See
        :meth:`openquake.hazardlib.geo.mesh.RectangularMesh.get_mean_inclination_and_azimuth`

        :returns:
            The average strike, in decimal degrees.
        """
        pass

    @classmethod
    def check_fault_data(cls, fault_trace, upper_seismogenic_depth,
                         lower_seismogenic_depth, dip, mesh_spacing):
        """
        Verify the fault data and raise ``ValueError`` if anything is wrong.

        This method doesn't have to be called by hands before creating the
        surface object, because it is called from :meth:`from_fault_data`.
        """
        if not len(fault_trace) >= 2:
            raise ValueError("the fault trace must have at least two points")
        if not fault_trace.horizontal():
            raise ValueError("the fault trace must be horizontal")
        tlats = [point.latitude for point in fault_trace.points]
        tlons = [point.longitude for point in fault_trace.points]
        if geo_utils.line_intersects_itself(tlons, tlats):
            raise ValueError("fault trace intersects itself")
        if not 0.0 < dip <= 90.0:
            raise ValueError("dip must be between 0.0 and 90.0")
        if not lower_seismogenic_depth > upper_seismogenic_depth:
            raise ValueError("lower seismogenic depth must be greater than "
                             "upper seismogenic depth")
        if not upper_seismogenic_depth >= fault_trace[0].depth:
            raise ValueError("upper seismogenic depth must be greater than "
                             "or equal to depth of fault trace")
        if not mesh_spacing > 0.0:
            raise ValueError("mesh spacing must be positive")

    @classmethod
    def from_profiles(cls, profiles, profile_sd, edge_sd, idl, align=False):
        """
        This creates a mesh from a set of profiles

        :param list profiles:
            A list of :class:`openquake.hazardlib.geo.Line.line` instances
        :param float profile_sd:
            The sampling distance along the profiles
        :param edge_sd:
            The sampling distance along the edges
        :param align:
            A boolean used to decide if profiles should be aligned at top
        :returns:
            A :class:`numpy.ndarray` instance with the coordinates of the mesh
        """

        # resample profiles
        rprofiles = []
        for prf in profiles:
            rprofiles.append(_resample_profile(prf, profile_sd))
        #
        # set the reference profile i.e. the longest one
        ref_idx = None
        max_length = -1e10
        for idx, prf in enumerate(rprofiles):
            length = prf.get_length()
            if length > max_length:
                max_length = length
                ref_idx = idx
        #
        # Check that in each profile the points are equally spaced
        for pro in rprofiles:
            pnts = [(pnt.longitude, pnt.latitude, pnt.depth) for pnt in pro.points]
            pnts = np.array(pnts)
            #
            assert np.all(pnts[:, 0] <= 180) & np.all(pnts[:, 0] >= -180)
            dst = distance(pnts[:-1, 0], pnts[:-1, 1], pnts[:-1, 2],
                           pnts[1:, 0], pnts[1:, 1], pnts[1:, 2])
            np.testing.assert_allclose(dst, profile_sd, rtol=1.)
        #
        # find the delta needed to align profiles if requested
        shift = np.zeros(len(rprofiles)-1)
        if align is True:
            for i in range(0, len(rprofiles)-1):
                shift[i] = profiles_depth_alignment(rprofiles[i], rprofiles[i+1])
        shift = np.array([0] + list(shift))
        #
        # find the maximum back-shift
        ccsum = [shift[0]]
        for i in range(1, len(shift)):
            ccsum.append(shift[i] + ccsum[i-1])
        add = ccsum - min(ccsum)
        #
        # Create resampled profiles. Now the profiles should be all aligned from
        # the top (if align option is True)
        rprof = []
        maxnum = 0
        for i, pro in enumerate(rprofiles):
            j = int(add[i])
            coo = get_coords(pro, idl)
            tmp = [[np.nan, np.nan, np.nan] for a in range(0, j)]
            if len(tmp):
                points = tmp + coo
            else:
                points = coo
            rprof.append(points)
            maxnum = max(maxnum, len(rprof[-1]))
        #
        # Now profiles will have the same number of samples (some of them can be
        # nan)
        for i, pro in enumerate(rprof):
            while len(pro) < maxnum:
                pro.append([np.nan, np.nan, np.nan])
            rprof[i] = np.array(pro)
        #
        # create mesh in forward direction
        prfr = get_mesh(rprof, ref_idx, edge_sd, idl)
        #
        # create the mesh in backward direction
        if ref_idx > 0:
            prfl = get_mesh_back(rprof, ref_idx, edge_sd, idl)
        else:
            prfl = []
        prf = prfl + prfr
        msh = np.array(prf)
        #
        # convert from profiles to edges
        msh = msh.swapaxes(0, 1)
        msh = fix_mesh(msh)
        return msh


def _resample_profile(line, sampling_dist):
    """
    :parameter line:
        An instance of :class:`openquake.hazardlib.geo.line.Line`
    :parameter sampling_dist:
        A scalar definining the distance used to sample the profile
    :returns:
        An instance of :class:`openquake.hazardlib.geo.line.Line`
    """
    lo = [pnt.longitude for pnt in line.points]
    la = [pnt.latitude for pnt in line.points]
    de = [pnt.depth for pnt in line.points]
    #
    # Set projection
    g = Geod(ellps='WGS84')
    #
    # Add a tolerance length to the last point of the profile
    # check that final portion of the profile is not vertical
    if abs(lo[-2]-lo[-1]) > 1e-5 and abs(la[-2]-la[-1]) > 1e-5:
        az12, az21, odist = g.inv(lo[-2], la[-2], lo[-1], la[-1])
        odist /= 1e3
        slope = np.arctan((de[-1] - de[-2]) / odist)
        hdist = TOLERANCE * sampling_dist * np.cos(slope)
        vdist = TOLERANCE * sampling_dist * np.sin(slope)
        endlon, endlat, backaz = g.fwd(lo[-1], la[-1], az12, hdist*1e3)
        lo[-1] = endlon
        la[-1] = endlat
        de[-1] = de[-1] + vdist
        az12, az21, odist = g.inv(lo[-2], la[-2], lo[-1], la[-1])
        # checking
        odist /= 1e3
        slopec = np.arctan((de[-1] - de[-2]) / odist)
        assert abs(slope-slopec) < 1e-3
    else:
        de[-1] = de[-1] + TOLERANCE * sampling_dist
    #
    # initialise the cumulated distance
    cdist = 0.
    #
    # get the azimuth of the profile
    azim = azimuth(lo[0], la[0], lo[-1], la[-1])
    #
    # initialise the list with the resampled nodes
    idx = 0
    resampled_cs = [Point(lo[idx], la[idx], de[idx])]
    #
    # set the starting point
    slo = lo[idx]
    sla = la[idx]
    sde = de[idx]
    #
    # resampling
    while 1:
        #
        # check loop exit condition
        if idx > len(lo)-2:
            break
        #
        # compute the distance between the starting point and the next point
        # on the profile
        segment_len = distance(slo, sla, sde, lo[idx+1], la[idx+1], de[idx+1])
        #
        # search for the point
        if cdist+segment_len > sampling_dist:
            #
            # this is the lenght of the last segment-fraction needed to
            # obtain the sampling distance
            delta = sampling_dist - cdist
            #
            # compute the slope of the last segment and its horizontal length.
            # We need to manage the case of a vertical segment TODO
            segment_hlen = distance(slo, sla, 0., lo[idx+1], la[idx+1], 0.)
            if segment_hlen > 1e-5:
                segment_slope = np.arctan((de[idx+1] - sde) / segment_hlen)
            else:
                segment_slope = 90.
            #
            # horizontal and vertical lenght of delta
            delta_v = delta * np.sin(segment_slope)
            delta_h = delta * np.cos(segment_slope)
            #
            # add a new point to the cross section
            pnts = npoints_towards(slo, sla, sde, azim, delta_h, delta_v, 2)
            #
            # update the starting point
            slo = pnts[0][-1]
            sla = pnts[1][-1]
            sde = pnts[2][-1]
            resampled_cs.append(Point(slo, sla, sde))
            #
            # reset the cumulative distance
            cdist = 0.

        else:
            cdist += segment_len
            idx += 1
            slo = lo[idx]
            sla = la[idx]
            sde = de[idx]
    #
    # check the distances along the profile
    coo = [[pnt.longitude, pnt.latitude, pnt.depth] for pnt in resampled_cs]
    coo = np.array(coo)
    for i in range(0, coo.shape[0]-1):
        dst = distance(coo[i, 0], coo[i, 1], coo[i, 2],
                       coo[i+1, 0], coo[i+1, 1], coo[i+1, 2])
        if abs(dst-sampling_dist) > 0.1*sampling_dist:
            raise ValueError('Wrong distance between points along the profile')
    #
    # 
    return Line(resampled_cs)
