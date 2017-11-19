# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
:mod:`openquake.hazardlib.calc.disagg` contains
:func:`disaggregation` as well as several aggregation functions for
extracting a specific PMF from the result of :func:`disaggregation`.
"""
from __future__ import division
import sys
import warnings
import operator
import collections
import numpy
import scipy.stats

from openquake.baselib.python3compat import raise_, range
from openquake.baselib.performance import Monitor
from openquake.baselib.general import AccumDict, pack, groupby
from openquake.hazardlib.calc import filters
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.geo.geodetic import npoints_between
from openquake.hazardlib.geo.utils import get_longitudinal_extent
from openquake.hazardlib.geo.utils import cross_idl
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.gsim.base import ContextMaker


def make_imldict(rlzs_by_gsim, imtls, iml_disagg, poes_disagg=(None,),
                 curves=None):
    """
    :returns: a dictionary poe, gsim, imt, rlzi -> iml

    If iml_disagg is given, poe is None and the values are all the same for a
    given imt for any gsim and rlzi.
    """
    if iml_disagg:
        poes_disagg = [None]
        iml_disagg = {from_string(imt): iml_disagg[imt]
                      for imt, iml in iml_disagg.items()}
    elif not curves:  # there could be no hazard for the given site
        return {}
    imldict = {}
    for poe in poes_disagg:
        for gsim in rlzs_by_gsim:
            for imt_str, imls in imtls.items():
                imt = from_string(imt_str)
                for rlzi in rlzs_by_gsim[gsim]:
                    imldict[poe, gsim, imt, rlzi] = numpy.interp(
                        poe, curves[rlzi][imt_str][::-1], imls[::-1]
                    ) if poe is not None else imls[0]
    return imldict


def collect_bins_data(trt_num, sources, site, cmaker, imldict,
                      truncation_level, n_epsilons, mon=Monitor()):
    sitecol = SiteCollection([site])
    # NB: instantiating truncnorm is slow and calls the infamous "doccer"
    truncnorm = scipy.stats.truncnorm(-truncation_level, truncation_level)
    acc = AccumDict(accum=[])
    for source in sources:
        try:
            trti = trt_num[source.tectonic_region_type]
            rupdict = cmaker.disaggregate(
                sitecol, source.iter_ruptures(), imldict, truncnorm,
                n_epsilons, mon)
            acc['trti'].extend([trti] * len(rupdict['mags']))
            acc += rupdict
        except Exception as err:
            etype, err, tb = sys.exc_info()
            msg = 'An error occurred with source id=%s. Error: %s'
            msg %= (source.source_id, err)
            raise_(etype, msg, tb)
    return acc


def lon_lat_bins(bb, coord_bin_width):
    """
    Define bin edges for disaggregation histograms.

    Given bins data as provided by :func:`collect_bins_data`, this function
    finds edges of histograms, taking into account maximum and minimum values
    of magnitude, distance and coordinates as well as requested sizes/numbers
    of bins.
    """
    west, south, east, north = bb
    west = numpy.floor(west / coord_bin_width) * coord_bin_width
    east = numpy.ceil(east / coord_bin_width) * coord_bin_width
    lon_extent = get_longitudinal_extent(west, east)
    lon_bins, _, _ = npoints_between(
        west, 0, 0, east, 0, 0,
        numpy.round(lon_extent / coord_bin_width + 1))
    lat_bins = coord_bin_width * numpy.arange(
        int(numpy.floor(south / coord_bin_width)),
        int(numpy.ceil(north / coord_bin_width) + 1))
    return lon_bins, lat_bins


def arrange_data_in_bins(bdata, bin_edges, kind, mon=Monitor):
    """
    :param bdata: a dictionary of probabilities of no exceedence
    :param bin_edges: bin edges
    :param kind: the kind of array to return, 'matrix' or 'pmf'
    :param mon: a Monitor instance
    :returns: a dictionary key -> matrix|pmf for each key in bdata
    """
    with mon('digitize'):
        mag_bins, dist_bins, lon_bins, lat_bins, eps_bins, trt_bins = bin_edges

        dim1 = len(mag_bins) - 1
        dim2 = len(dist_bins) - 1
        dim3 = len(lon_bins) - 1
        dim4 = len(lat_bins) - 1
        shape = (dim1, dim2, dim3, dim4, len(eps_bins) - 1, len(trt_bins))

        # find bin indexes of rupture attributes; bins are assumed closed
        # on the lower bound, and open on the upper bound, that is [ )
        # longitude values need an ad-hoc method to take into account
        # the 'international date line' issue
        # the 'minus 1' is needed because the digitize method returns the
        # index of the upper bound of the bin
        mags_idx = numpy.digitize(bdata.mags, mag_bins) - 1
        dists_idx = numpy.digitize(bdata.dists, dist_bins) - 1
        lons_idx = _digitize_lons(bdata.lons, lon_bins)
        lats_idx = numpy.digitize(bdata.lats, lat_bins) - 1

        # because of the way numpy.digitize works, values equal to the last bin
        # edge are associated to an index equal to len(bins) which is not a
        # valid index for the disaggregation matrix. Such values are assumed
        # to fall in the last bin
        mags_idx[mags_idx == dim1] = dim1 - 1
        dists_idx[dists_idx == dim2] = dim2 - 1
        lons_idx[lons_idx == dim3] = dim3 - 1
        lats_idx[lats_idx == dim4] = dim4 - 1

    # aggregate probabilities
    out = {}
    cache = {}
    cache_hit = 0
    for k, pnes in bdata.items():
        cache_key = pnes.sum()
        try:
            array = cache[cache_key]
            cache_hit += 1
        except KeyError:
            mat = numpy.ones(shape)
            for i_mag, i_dist, i_lon, i_lat, i_trt, pne in zip(
                    mags_idx, dists_idx, lons_idx, lats_idx, bdata.trti, pnes):
                mat[i_mag, i_dist, i_lon, i_lat, :, i_trt] *= pne
            matrix = 1. - mat
            pmf = numpy.array([fn(matrix) for fn in pmf_map.values()])
            cache[cache_key] = array = matrix if kind == 'matrix' else pmf
        out[k] = array
    mon.cache_info = numpy.array([len(bdata), cache_hit])  # operations, hits
    return out


def _digitize_lons(lons, lon_bins):
    """
    Return indices of the bins to which each value in lons belongs.
    Takes into account the case in which longitude values cross the
    international date line.

    :parameter lons:
        An instance of `numpy.ndarray`.
    :parameter lons_bins:
        An instance of `numpy.ndarray`.
    """
    if cross_idl(lon_bins[0], lon_bins[-1]):
        idx = numpy.zeros_like(lons, dtype=numpy.int)
        for i_lon in range(len(lon_bins) - 1):
            extents = get_longitudinal_extent(lons, lon_bins[i_lon + 1])
            lon_idx = extents > 0
            if i_lon != 0:
                extents = get_longitudinal_extent(lon_bins[i_lon], lons)
                lon_idx &= extents >= 0
            idx[lon_idx] = i_lon
        return numpy.array(idx)
    else:
        return numpy.digitize(lons, lon_bins) - 1


def disaggregation(
        sources, site, imt, iml, gsim_by_trt, truncation_level,
        n_epsilons, mag_bin_width, dist_bin_width, coord_bin_width,
        source_filter=filters.source_site_noop_filter):
    """
    Compute "Disaggregation" matrix representing conditional probability of an
    intensity mesaure type ``imt`` exceeding, at least once, an intensity
    measure level ``iml`` at a geographical location ``site``, given rupture
    scenarios classified in terms of:

    - rupture magnitude
    - Joyner-Boore distance from rupture surface to site
    - longitude and latitude of the surface projection of a rupture's point
      closest to ``site``
    - epsilon: number of standard deviations by which an intensity measure
      level deviates from the median value predicted by a GSIM, given the
      rupture parameters
    - rupture tectonic region type

    In other words, the disaggregation matrix allows to compute the probability
    of each scenario with the specified properties (e.g., magnitude, or the
    magnitude and distance) to cause one or more exceedences of a given hazard
    level.

    For more detailed information about the disaggregation, see for instance
    "Disaggregation of Seismic Hazard", Paolo Bazzurro, C. Allin Cornell,
    Bulletin of the Seismological Society of America, Vol. 89, pp. 501-520,
    April 1999.

    :param sources:
        Seismic source model, as for
        :mod:`PSHA <openquake.hazardlib.calc.hazard_curve>` calculator it
        should be an iterator of seismic sources.
    :param site:
        :class:`~openquake.hazardlib.site.Site` of interest to calculate
        disaggregation matrix for.
    :param imt:
        Instance of :mod:`intensity measure type <openquake.hazardlib.imt>`
        class.
    :param iml:
        Intensity measure level. A float value in units of ``imt``.
    :param gsim_by_trt:
        Tectonic region type to GSIM objects mapping.
    :param truncation_level:
        Float, number of standard deviations for truncation of the intensity
        distribution.
    :param n_epsilons:
        Integer number of epsilon histogram bins in the result matrix.
    :param mag_bin_width:
        Magnitude discretization step, width of one magnitude histogram bin.
    :param dist_bin_width:
        Distance histogram discretization step, in km.
    :param coord_bin_width:
        Longitude and latitude histograms discretization step,
        in decimal degrees.
    :param source_filter:
        Optional source-site filter function. See
        :mod:`openquake.hazardlib.calc.filters`.

    :returns:
        A tuple of two items. First is itself a tuple of bin edges information
        for (in specified order) magnitude, distance, longitude, latitude,
        epsilon and tectonic region types.

        Second item is 6d-array representing the full disaggregation matrix.
        Dimensions are in the same order as bin edges in the first item
        of the result tuple. The matrix can be used directly by pmf-extractor
        functions.
    """
    trts = sorted(set(src.tectonic_region_type for src in sources))
    trt_num = dict((trt, i) for i, trt in enumerate(trts))
    rlzs_by_gsim = {gsim_by_trt[trt]: [0] for trt in trts}
    cmaker = ContextMaker(rlzs_by_gsim, source_filter.integration_distance)
    imldict = make_imldict(rlzs_by_gsim, {str(imt): [iml]}, {str(imt): iml})
    by_trt = groupby(sources, operator.attrgetter('tectonic_region_type'))
    bdata = {}
    for trt, srcs in by_trt.items():
        bdata[trt] = collect_bins_data(
            trt_num, srcs, site, cmaker, imldict, truncation_level, n_epsilons)
    bd = pack(sum(bdata.values(), {}), 'mags dists lons lats trti'.split())
    if len(bd.mags) == 0:
        warnings.warn(
            'No ruptures have contributed to the hazard at site %s'
            % site, RuntimeWarning)
        return None, None

    mag_bins = mag_bin_width * numpy.arange(
        int(numpy.floor(bd.mags.min() / mag_bin_width)),
        int(numpy.ceil(bd.mags.max() / mag_bin_width) + 1))

    dist_bins = dist_bin_width * numpy.arange(
        int(numpy.floor(bd.dists.min() / dist_bin_width)),
        int(numpy.ceil(bd.dists.max() / dist_bin_width) + 1))

    bb = (bd.lons.min(), bd.lons.min(), bd.lats.max(), bd.lats.max())
    lon_bins, lat_bins = lon_lat_bins(bb, coord_bin_width)

    eps_bins = numpy.linspace(-truncation_level, truncation_level,
                              n_epsilons + 1)

    bin_edges = (mag_bins, dist_bins, lon_bins, lat_bins, eps_bins, trts)
    matrix = numpy.zeros((len(mag_bins) - 1, len(dist_bins) - 1,
                          len(lon_bins) - 1, len(lat_bins) - 1,
                          len(eps_bins) - 1, len(trts)))
    for trt in bdata:
        bd = pack(bdata[trt], 'mags dists lons lats trti'.split())
        [mat] = arrange_data_in_bins(bd, bin_edges, 'matrix').values()
        matrix[..., trt_num[trt]] = mat[..., trt_num[trt]]
    return bin_edges, matrix


def mag_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude PMF.

    :returns:
        1d array, a histogram representing magnitude PMF.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    mag_pmf = numpy.zeros(nmags)
    for i in range(nmags):
        mag_pmf[i] = numpy.prod(
            [1 - matrix[i][j][k][l][m][n]
             for j in range(ndists)
             for k in range(nlons)
             for l in range(nlats)
             for m in range(neps)
             for n in range(ntrts)])
    return 1 - mag_pmf


def dist_pmf(matrix):
    """
    Fold full disaggregation matrix to distance PMF.

    :returns:
        1d array, a histogram representing distance PMF.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    dist_pmf = numpy.zeros(ndists)
    for j in range(ndists):
        dist_pmf[j] = numpy.prod(
            [1 - matrix[i][j][k][l][m][n]
             for i in range(nmags)
             for k in range(nlons)
             for l in range(nlats)
             for m in range(neps)
             for n in range(ntrts)])
    return 1 - dist_pmf


def trt_pmf(matrix):
    """
    Fold full disaggregation matrix to tectonic region type PMF.

    :returns:
        1d array, a histogram representing tectonic region type PMF.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    trt_pmf = numpy.zeros(ntrts)
    for n in range(ntrts):
        trt_pmf[n] = numpy.prod(
            [1 - matrix[i][j][k][l][m][n]
             for i in range(nmags)
             for j in range(ndists)
             for k in range(nlons)
             for l in range(nlats)
             for m in range(neps)])
    return 1 - trt_pmf


def mag_dist_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude / distance PMF.

    :returns:
        2d array. First dimension represents magnitude histogram bins,
        second one -- distance histogram bins.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    mag_dist_pmf = numpy.zeros((nmags, ndists))
    for i in range(nmags):
        for j in range(ndists):
            mag_dist_pmf[i][j] = numpy.prod(
                [1 - matrix[i][j][k][l][m][n]
                 for k in range(nlons)
                 for l in range(nlats)
                 for m in range(neps)
                 for n in range(ntrts)])
    return 1 - mag_dist_pmf


def mag_dist_eps_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude / distance / epsilon PMF.

    :returns:
        3d array. First dimension represents magnitude histogram bins,
        second one -- distance histogram bins, third one -- epsilon
        histogram bins.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    mag_dist_eps_pmf = numpy.zeros((nmags, ndists, neps))
    for i in range(nmags):
        for j in range(ndists):
            for m in range(neps):
                mag_dist_eps_pmf[i][j][m] = numpy.prod(
                    [1 - matrix[i][j][k][l][m][n]
                     for k in range(nlons)
                     for l in range(nlats)
                     for n in range(ntrts)]
                )
    return 1 - mag_dist_eps_pmf


def lon_lat_pmf(matrix):
    """
    Fold full disaggregation matrix to longitude / latitude PMF.

    :returns:
        2d array. First dimension represents longitude histogram bins,
        second one -- latitude histogram bins.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    lon_lat_pmf = numpy.zeros((nlons, nlats))
    for k in range(nlons):
        for l in range(nlats):
            lon_lat_pmf[k][l] = numpy.prod(
                [1 - matrix[i][j][k][l][m][n]
                 for i in range(nmags)
                 for j in range(ndists)
                 for m in range(neps)
                 for n in range(ntrts)])
    return 1 - lon_lat_pmf


def mag_lon_lat_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude / longitude / latitude PMF.

    :returns:
        3d array. First dimension represents magnitude histogram bins,
        second one -- longitude histogram bins, third one -- latitude
        histogram bins.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    mag_lon_lat_pmf = numpy.zeros((nmags, nlons, nlats))
    for i in range(nmags):
        for k in range(nlons):
            for l in range(nlats):
                mag_lon_lat_pmf[i][k][l] = numpy.prod(
                    [1 - matrix[i][j][k][l][m][n]
                     for j in range(ndists)
                     for m in range(neps)
                     for n in range(ntrts)])
    return 1 - mag_lon_lat_pmf


def lon_lat_trt_pmf(matrix):
    """
    Fold full disaggregation matrix to longitude / latitude / tectonic region
    type PMF.

    :returns:
        3d array. Dimension represent longitude, latitude and tectonic region
        type histogram bins respectively.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    lon_lat_trt_pmf = numpy.zeros((nlons, nlats, ntrts))
    for k in range(nlons):
        for l in range(nlats):
            for n in range(ntrts):
                lon_lat_trt_pmf[k][l][n] = numpy.prod(
                    [1 - matrix[i][j][k][l][m][n]
                     for i in range(nmags)
                     for j in range(ndists)
                     for m in range(neps)])
    return 1 - lon_lat_trt_pmf


# this dictionary is useful to extract a fixed set of
# submatrices from the full disaggregation matrix
pmf_map = collections.OrderedDict([
    (('Mag', ), mag_pmf),
    (('Dist', ), dist_pmf),
    (('TRT', ), trt_pmf),
    (('Mag', 'Dist'), mag_dist_pmf),
    (('Mag', 'Dist', 'Eps'), mag_dist_eps_pmf),
    (('Lon', 'Lat'), lon_lat_pmf),
    (('Mag', 'Lon', 'Lat'), mag_lon_lat_pmf),
    (('Lon', 'Lat', 'TRT'), lon_lat_trt_pmf),
])
