# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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
:module:`openquake.hazardlib.gsim.can15.utils` contains utility
functions required for the implementation of CAN15 gmpes
"""
import copy
import scipy
import numpy as np


def get_rup_len_west(mag):
    """ Rupture length from WC1994 - See Atkinson (2012) Appendix A"""
    return 10**(-2.44+0.59*mag)


def get_rup_wid_west(mag):
    """ Rupture width from WC1994 - See Atkinson (2012) Appendix A"""
    return 10**(-1.01+0.32*mag)


def get_rup_len_east(mag):
    """ Rupture length from WC1994 - See Atkinson (2012) Appendix A"""
    return get_rup_len_west(mag)*0.6


def get_rup_wid_east(mag):
    """ Rupture width from WC1994 - See Atkinson (2012) Appendix A"""
    return get_rup_wid_west(mag)*0.6


def _get_equivalent_distances_east(wid, lng, mag, repi, focal_depth=10.,
                                   ab06=False):
    """
    Computes equivalent values of Joyner-Boore and closest distance to the
    rupture given epoicentral distance. The procedure is described in
    Atkinson (2012) - Appendix A (page 32).

    :param float wid:
        Width of rectangular rupture
    :param float lng:
        Length of rectangular rupture
    :param float mag:
        Magnitude
    :param repi:
        A :class:`numpy.ndarray` instance containing repi values
    :param float focal_depth:
        Focal depth
    :param boolean ab06:
        When true a minimum ztor value is set to force near-source saturation
    """
    dtop = focal_depth - 0.5*wid
    # this computes a minimum ztor value - used for AB2006
    if ab06:
        ztor_ab06 = 21-2.5*mag
        dtop = np.max([ztor_ab06, dtop])
    ztor = np.maximum(dtop, 0)
    # find the average distance to the fault projection
    dsurf = np.maximum(repi - 0.3 * lng, 0.1)
    # rrup
    rrup = (dsurf**2+ztor**2)**0.5
    # return rjb and rrup
    return dsurf, rrup


def get_equivalent_distances_east(mag, repi, focal_depth=10., ab06=False):
    wid = get_rup_wid_east(mag)
    lng = get_rup_len_east(mag)
    rjb, rrup = _get_equivalent_distances_east(wid, lng, mag, repi,
                                               focal_depth, ab06)
    return rjb, rrup


def add_distances_east(ctx, focal_depth=10., ab06=False):
    """
    :returns: a new context with distances .rjb and .rrup computed from .repi
    """
    ctx = copy.copy(ctx)
    wid = get_rup_wid_east(ctx.mag)
    lng = get_rup_len_east(ctx.mag)
    ctx.rjb, ctx.rrup = _get_equivalent_distances_east(
        wid, lng, ctx.mag, ctx.repi, focal_depth, ab06)
    return ctx


def get_equivalent_distances_west(mag, repi, focal_depth=10.):
    wid = get_rup_wid_west(mag)
    lng = get_rup_len_west(mag)
    rjb, rrup = _get_equivalent_distances_east(wid, lng, mag, repi,
                                               focal_depth, ab06=False)
    return rjb, rrup


def get_equivalent_distance_inslab(mag, repi, hslab):
    """
    :param float mag:
        Magnitude
    :param repi:
        A :class:`numpy.ndarray` instance containing repi values
    :param float hslab:
        Depth of the slab
    """
    area = 10**(-3.225+0.89*mag)
    radius = (area / scipy.constants.pi)**0.5
    rjb = np.maximum(repi - radius, 0.)
    rrup = (rjb**2+hslab**2)**0.5
    return rjb, rrup
