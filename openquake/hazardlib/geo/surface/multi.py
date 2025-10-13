# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
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
Module :mod:`openquake.hazardlib.geo.surface.multi` defines
:class:`MultiSurface`.
"""
import numpy as np
from shapely.geometry import Polygon
from openquake.baselib.performance import Monitor
from openquake.hazardlib.geo.surface.base import BaseSurface
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo import utils
from openquake.hazardlib import geo
from openquake.hazardlib.geo.surface import PlanarSurface

F32 = np.float32
MSPARAMS = ['area', 'dip', 'strike', 'u_max', 'width', 'zbot', 'ztor',
            'tl0', 'tl1', 'tr0', 'tr1', 'west', 'east', 'north', 'south']
MS_DT = [(p, np.float32) for p in MSPARAMS] + [('hypo', (F32, 3))]


# really fast
def build_secparams(sections):
    """
    :returns: an array of section parameters
    """
    secparams = np.zeros(len(sections), MS_DT)
    for sparam, sec in zip(secparams, sections):
        sparam['area'] = sec.get_area()
        sparam['dip'] = sec.get_dip()
        sparam['strike'] = sec.get_strike()
        sparam['width'] = sec.get_width()
        sparam['ztor'] = sec.get_top_edge_depth()
        sparam['zbot'] = sec.mesh.depths.max()
        sparam['tl0'] = sec.tor.coo[0, 0]
        sparam['tl1'] = sec.tor.coo[0, 1]
        sparam['tr0'] = sec.tor.coo[-1, 0]
        sparam['tr1'] = sec.tor.coo[-1, 1]

        bb = sec.get_bounding_box()
        sparam['west'] = bb[0]
        sparam['east'] = bb[1]
        sparam['north'] = bb[2]
        sparam['south'] = bb[3]

        mid = sec.get_middle_point()
        sparam['hypo'] = (mid.x, mid.y, mid.z)
    return secparams


# not fast
def build_msparams(rupture_idxs, secparams, close_sec=None, ry0=False,
                   mon1=Monitor(), mon2=Monitor()):
    """
    :returns: a structured array of parameters
    """
    U = len(rupture_idxs)  # number of ruptures
    msparams = np.zeros(U, MS_DT)
    if close_sec is None:
        # NB: in the engine close_sec is computed in the preclassical phase
        close_sec = np.ones(len(secparams), bool)

    # building lines, very fast
    with mon1:
        lines = []
        for secparam in secparams:
            tl0, tl1, tr0, tr1 = secparam[['tl0', 'tl1', 'tr0', 'tr1']]
            line = geo.Line.from_coo(np.array([[tl0, tl1], [tr0, tr1]], float))
            lines.append(line)

    # building msparams, slow due to the computation of u_max
    with mon2:
        for msparam, idxs in zip(msparams, rupture_idxs):
            idxs = idxs[close_sec[idxs]]
            if len(idxs) == 0:  # all sections are far away
                continue

            # building u_max
            tors = [lines[idx] for idx in idxs]
            if ry0:
                msparam['u_max'] = geo.MultiLine(tors).get_u_max()

            # building simple multisurface params
            secparam = secparams[idxs]
            areas = secparam['area']
            msparam['area'] = areas.sum()
            ws = areas / msparam['area']  # weights
            msparam['dip'] = ws @ secparam['dip']
            msparam['strike'] = utils.angular_mean_weighted(
                secparam['strike'], ws) % 360
            msparam['width'] = ws @ secparam['width']
            msparam['ztor'] = ws @ secparam['ztor']
            msparam['zbot'] = ws @ secparam['zbot']

            # building bounding box
            lons = np.concatenate([secparam['west'], secparam['east']])
            lats = np.concatenate([secparam['north'], secparam['south']])
            bb = utils.get_spherical_bounding_box(lons, lats)
            msparam['west'] = bb[0]
            msparam['east'] = bb[1]
            msparam['north'] = bb[2]
            msparam['south'] = bb[3]

    return msparams


class MultiSurface(BaseSurface):
    """
    Represent a surface as a collection of independent surface elements.

    :param surfaces:
        List of instances of subclasses of
        :class:`~openquake.hazardlib.geo.surface.base.BaseSurface`
        each representing a surface geometry element.
    """

    @property
    def surface_nodes(self):
        """
        :returns:
            a list of surface nodes from the underlying single node surfaces
        """
        if type(self.surfaces[0]).__name__ == 'PlanarSurface':
            return [surf.surface_nodes[0] for surf in self.surfaces]
        return [surf.surface_nodes for surf in self.surfaces]

    @classmethod
    def from_csv(cls, fname: str):
        """
        :param fname:
            path to a CSV file with header (lon, lat, dep) and 4 x P
            rows describing planes in terms of corner points in the order
            topleft, topright, bottomright, bottomleft
        :returns:
            a MultiSurface made of P planar surfaces
        """
        surfaces = []
        tmp = np.genfromtxt(fname, delimiter=',', comments='#', skip_header=1)
        tmp = tmp.reshape(-1, 4, 3, order='A')
        for i in range(tmp.shape[0]):
            arr = tmp[i, :, :]
            surfaces.append(PlanarSurface.from_ucerf(arr))
        return cls(surfaces)

    # NB: called in event_based calculations
    @property
    def mesh(self):
        """
        :returns: mesh corresponding to the whole multi surface
        """
        lons = []
        lats = []
        deps = []
        for m in [surface.mesh for surface in self.surfaces]:
            ok = np.isfinite(m.lons) & np.isfinite(m.lats)
            lons.append(m.lons[ok])
            lats.append(m.lats[ok])
            deps.append(m.depths[ok])
        return Mesh(np.concatenate(lons), np.concatenate(lats),
                    np.concatenate(deps))

    def __init__(self, surfaces, msparam=None):
        """
        Intialize a multi surface object from a list of surfaces

        :param surfaces:
            A list of instances of subclasses of
            :class:`openquake.hazardlib.geo.surface.BaseSurface`
        """
        self.surfaces = surfaces
        if msparam is None:
            # slow operation: happens only in hazardlib, NOT in the engine
            secparams = build_secparams(self.surfaces)
            idxs = np.arange(len(self.surfaces))
            self.msparam = build_msparams([idxs], secparams)[0]
        else:
            self.msparam = msparam
        self.tor = geo.MultiLine([s.tor for s in self.surfaces])

    def get_min_distance(self, mesh):
        """
        For each point in ``mesh`` compute the minimum distance to each
        surface element and return the smallest value.
        See :meth:`superclass method
        <.base.BaseSurface.get_min_distance>`
        for spec of input and result values.
        """
        dists = [surf.get_min_distance(mesh) for surf in self.surfaces]
        return np.min(dists, axis=0)

    def get_joyner_boore_distance(self, mesh):
        """
        For each point in mesh compute the Joyner-Boore distance to all the
        surface elements and return the smallest value.
        See :meth:`superclass method
        <.base.BaseSurface.get_joyner_boore_distance>`
        for spec of input and result values.
        """
        # For each point in mesh compute the Joyner-Boore distance to all the
        # surfaces and return the shortest one.
        dists = [
            surf.get_joyner_boore_distance(mesh) for surf in self.surfaces]
        return np.min(dists, axis=0)

    def get_top_edge_depth(self):
        """
        Compute top edge depth of each surface element and return area-weighted
        average value (in km).
        """
        return self.msparam['ztor']

    def get_strike(self):
        """
        Compute strike of each surface element and return area-weighted average
        value (in range ``[0, 360]``) using formula from:
        http://en.wikipedia.org/wiki/Mean_of_circular_quantities
        Note that the original formula has been adapted to compute a weighted
        rather than arithmetic mean.
        """
        return self.msparam['strike']

    def get_dip(self):
        """
        Compute dip of each surface element and return area-weighted average
        value (in range ``(0, 90]``).
        Given that dip values are constrained in the range (0, 90], the simple
        formula for weighted mean is used.
        """
        return self.msparam['dip']

    def get_width(self):
        """
        Compute width of each surface element, and return area-weighted
        average value (in km).
        """
        return self.msparam['width']

    def get_area(self):
        """
        Return sum of surface elements areas (in squared km).
        """
        return self.msparam['area']

    def get_bounding_box(self):
        """
        Compute bounding box for each surface element, and then return
        the bounding box of all surface elements' bounding boxes.

        :return:
           A tuple of four items. These items represent western, eastern,
           northern and southern borders of the bounding box respectively.
           Values are floats in decimal degrees.
        """
        return self.msparam[['west', 'east', 'north', 'south']]

    def get_middle_point(self):
        """
        If :class:`MultiSurface` is defined by a single surface, simply
        returns surface's middle point, otherwise find surface element closest
        to the surface's bounding box centroid and return corresponding
        middle point.
        Note that the concept of middle point for a multi surface is ambiguous
        and alternative definitions may be possible. However, this method is
        mostly used to define the hypocenter location for ruptures described
        by a multi surface
        (see :meth:`openquake.hazardlib.source.characteristic.CharacteristicFaultSource.iter_ruptures`).
        This is needed because when creating fault based sources, the rupture's
        hypocenter locations are not explicitly defined, and therefore an
        automated way to define them is required.
        """
        if len(self.surfaces) == 1:
            return self.surfaces[0].get_middle_point()
        west, east, north, south = self.get_bounding_box()
        midlon, midlat = utils.get_middle_point(west, north, east, south)
        m = Mesh(np.array([midlon]), np.array([midlat]))
        dists = [surf.get_min_distance(m) for surf in self.surfaces]
        return self.surfaces[np.argmin(dists)].get_middle_point()

    def get_surface_boundaries(self):
        los, las = self.surfaces[0].get_surface_boundaries()
        poly = Polygon((lo, la) for lo, la in zip(los, las))
        for i in range(1, len(self.surfaces)):
            los, las = self.surfaces[i].get_surface_boundaries()
            polyt = Polygon([(lo, la) for lo, la in zip(los, las)])
            poly = poly.union(polyt)
        coo = np.array([[lo, la] for lo, la in list(poly.exterior.coords)])
        return coo[:, 0], coo[:, 1]

    def get_surface_boundaries_3d(self):
        lons = []
        lats = []
        deps = []
        conc = np.concatenate
        for surf in self.surfaces:
            coo = surf.get_surface_boundaries_3d()
            lons.append(coo[0])
            lats.append(coo[1])
            deps.append(coo[2])
        return conc(lons), conc(lats), conc(deps)

    def get_rx_distance(self, mesh):
        """
        :param mesh:
            An instance of :class:`openquake.hazardlib.geo.mesh.Mesh` with the
            coordinates of the sites.
        :returns:
            A :class:`numpy.ndarray` instance with the Rx distance. Note that
            the Rx distance is directly taken from the GC2 t-coordinate.
        """
        tut, _uut = self.tor.get_tu(mesh.lons, mesh.lats)
        rx = tut[0] if len(tut[0].shape) > 1 else tut
        return rx

    def get_ry0_distance(self, mesh):
        """
        :param mesh:
            An instance of :class:`openquake.hazardlib.geo.mesh.Mesh` with the
            coordinates of the sites.
        """
        u_max = self.tor.get_u_max()
        _tut, uut = self.tor.get_tu(mesh.lons, mesh.lats)
        ry0 = np.zeros_like(uut)
        ry0[uut < 0] = np.abs(uut[uut < 0])
        condition = uut > u_max
        ry0[condition] = uut[condition] - u_max
        return ry0
