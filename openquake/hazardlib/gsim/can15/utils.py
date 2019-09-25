"""
:module:`openquake.hazardlib.gsim.can15.utils` contains utility
functions required for the implementation of CAN15 gmpes
"""

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
    ztor = max(0, dtop)
    # find the average distance to the fault projection
    dsurf = np.max([repi-0.3*lng, 0.1*np.ones_like(repi)], axis=0)
    # rrup
    rrup = (dsurf**2+ztor**2)**0.5
    # return rjb and rrup
    return dsurf, rrup


def get_equivalent_distances_east(mag, repi, focal_depth=10., ab06=False):
    """ """
    wid = get_rup_wid_east(mag)
    lng = get_rup_len_east(mag)
    rjb, rrup = _get_equivalent_distances_east(wid, lng, mag, repi,
                                               focal_depth, ab06)
    return rjb, rrup


def get_equivalent_distances_west(mag, repi, focal_depth=10.):
    """ """
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
    rjb = np.max([repi-radius, np.zeros_like(repi)], axis=0)
    rrup = (rjb**2+hslab**2)**0.5
    return rjb, rrup
