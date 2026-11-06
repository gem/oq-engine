# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
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
Calibration of ps_grid_spacing and pointsource_distance, performed in
preclassical when the user sets ``ps_grid_spacing = auto``, or only of the
pointsource_distance when the user sets a ps_grid_spacing without a
pointsource_distance.

The rates of the point sources are computed on a sample of sites evenly
spread over the region (with a single GMPE per group, two IMTs and a
maximum distance cut to MAXDIST), both for a reference setting (no
gridding and pointsource_distance = 100 km) and for a set of candidate
pairs (ps_grid_spacing, pointsource_distance); the cheapest candidate with
a 99th percentile of the relative error on the hazard maps below a
tolerance is chosen or, if there is none, the cheapest candidate with an
error close to the smallest one.
"""
import time
import logging
from collections import namedtuple
import numpy
from openquake.baselib import parallel
from openquake.baselib.general import (
    AccumDict, WeightedSequence, block_splitter)
from openquake.hazardlib.map_array import compute_hmaps
from openquake.hazardlib.calc.mean_rates import to_probs
from openquake.hazardlib.source.point import grid_point_sources
from openquake.hazardlib.source.multi_point import get
from openquake.hazardlib.calc.filters import split_source, magdepdist
from openquake.hazardlib.contexts import PAIR_COST
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.site import SiteCollection

Candidate = namedtuple('Candidate',
    'ps_grid_spacing pointsource_distance time weight mean_err p99_err')

GRID_SPACINGS = [50., 25., 15.]  # candidate values in km
PS_DISTANCES = [15., 25., 50., 75.]  # candidate values in km
# reference (ps_grid_spacing, pointsource_distance): no gridding and
# pointsource_distance = 100 km; using 1000 km would be exact but too
# expensive with large maximum distances (e.g. in AUS)
REFERENCE = (0., 100.)
TOLERANCE = .05  # on the 99th percentile of the relative error
MIN_HMAP = .01  # ignore the hazard maps below this value (in g)
# the calibration uses only the IMTs with the periods closest to these:
# the largest errors are at 0.2 s in SAM and at 1.0 s in Tonga
PERIODS = [.2, 1.]
LEVEL_STEP = 2  # use one hazard level every LEVEL_STEP in the calibration
NSITES = 300  # size of the sample of sites
MAXDIST = 300.  # in km, maximum distance used in the calibration
# when no candidate is within the tolerance, the candidates with an error
# up to 10% larger than the smallest one are considered equivalent
CLOSE = .1
# the points of a cell are within a diagonal from the location of the
# collapsed point source, which is inside the cell
DIAGONAL = numpy.sqrt(2) * max(GRID_SPACINGS)


def calibration(srcs, sites, cmaker, keys, monitor):
    """
    :param keys: pairs (ps_grid_spacing, pointsource_distance) with the
                 same spacing, sorted by distance
    :returns: a dictionary key -> AccumDict(rates, time, weight), with
              rates of shape (N, L), for Starmap.reduce

    The weight is computed as in ContextMaker.estimate_weight, from the
    number of contexts and (rupture, site) pairs; unlike the time on the
    sample, it ranks correctly the cost of the full calculation
    """
    t0 = time.time()
    cmaker.init_monitoring(monitor)
    psds = [psd for _psgs, psd in keys]
    # the contexts for the different distances are built at once, sharing
    # the ruptures, which is much faster
    ctxs = cmaker.from_srcs(srcs, sites, psds)  # sets src.nsites
    pairs = sum(src.num_ruptures * src.nsites for src in srcs)
    dt = (time.time() - t0) / len(keys)  # the contexts are shared
    out = {}
    for key, psd in zip(keys, psds):
        rates = numpy.zeros((len(sites), cmaker.imtls.size))
        if len(ctxs[psd]):
            rmap = cmaker.get_rmap(ctxs[psd])
            rates[rmap.sids] = rmap.array[:, :, 0]  # there is a single gsim
        out[key] = AccumDict(dict(rates=rates, time=dt,
                                  weight=len(ctxs[psd]) + pairs / PAIR_COST))
    return out


# the points farther than the maximum distance plus the margin from all
# the sample sites are ignored; the engine keeps a (collapsed) point
# source if its location is within the maximum distance plus its
# max_radius from a site, so the margin keeps complete the grid cells
# crossing the maximum distance; NB: the points of an area source have
# all the same max_radius, so only the first point is considered
def _get_margin(sg, maxdist):
    radius = 0.
    for src in sg:
        if src.code == b'M' and not src.bysrc_unc:
            radius = max(radius, _multipoint_radius(src, maxdist))
        elif src.code == b'A' and not src.bysrc_unc:
            radius = max(radius, next(iter(src)).max_radius(maxdist))
        elif src.code == b'P':
            radius = max(radius, src.max_radius(maxdist))
    return DIAGONAL + radius


# the points of a multipoint source differ only by MFD and aspect ratio,
# so the radius is computed once for each pair (maximum magnitude, aspect
# ratio), without building a PointSource for each point (slow)
def _multipoint_radius(src, maxdist):
    point = next(iter(src))
    radii = {}
    for i, mfd in enumerate(src.mfd):
        # ignoring the zero rates, as in get_annual_occurrence_rates
        mag, rate = [(m, r) for m, r in mfd.get_annual_occurrence_rates()
                     if r > 0][-1]
        rar = get(src.rupture_aspect_ratio, i)
        if (mag, rar) not in radii:
            point.rupture_aspect_ratio = rar
            radii[mag, rar] = point.max_radius(
                maxdist, point._get_rupture_projection_radii([(rate, mag)]))
    return max(radii.values())


# split the area and multipoint sources in point sources, keeping only
# the points close to the sample sites (a source without close points is
# not split at all, which is important since splitting is slow); the
# point sources of the composite source model are not modified; a source
# with a single point is not split by split_source, so it is not gridded
# by the engine and it is ignored, since it gives no gridding error
def _get_points(sg, sites, maxdist):
    dist = maxdist + _get_margin(sg, maxdist)
    points = []
    for src in sg:
        if src.code in b'AM' and not src.bysrc_unc:
            mesh = (src.mesh if src.code == b'M' else
                    src.polygon.discretize(src.area_discretization))
            if sites.count_close(Mesh(mesh.lons, mesh.lats), dist).any():
                points.extend(s for s in split_source(src) if s.code == b'P')
        elif src.code == b'P':
            points.append(src)
    if points:
        mesh = Mesh.from_coords(
            [(p.location.x, p.location.y) for p in points], sort=False)
        close = sites.count_close(mesh, dist)
        points = [p for p, c in zip(points, close) if c]
    return points


# split the sources of the groups, gridded with the given spacing, in
# WeightedSequences of sources; the blocks are balanced by number
# of ruptures times number of sites within the maximum distance from the
# location of the source
def _get_blocks(groups, sites, cmakers, psgs, num_tasks):
    pairs = []  # (src, weight), grouped by grp_id
    for grp_id, points in groups.items():
        srcs = grid_point_sources(points, psgs)
        mesh = Mesh.from_coords(
            [(src.location.x, src.location.y) for src in srcs], sort=False)
        nsites = sites.count_close(
            mesh, cmakers[grp_id].maximum_distance.y[-1])
        pairs.extend((src, src.num_ruptures * (n + 1))
                     for src, n in zip(srcs, nsites))
    maxweight = sum(w for _, w in pairs) / num_tasks
    return [WeightedSequence(blk) for blk in block_splitter(
        pairs, maxweight, lambda p: p[1], lambda p: p[0].grp_id)]


# the IMTs with the periods closest to PERIODS, or all the IMTs if there
# are less than 3 IMTs with a period (PGA included)
def _calib_imts(oq):
    imts = oq.imt_periods()
    if len(imts) < 3:
        return list(oq.imtls)
    periods = numpy.array([imt.period for imt in imts])
    chosen = {imts[numpy.abs(periods - period).argmin()].string
              for period in PERIODS}
    return [imt for imt in oq.imtls if imt in chosen]


# ContextMaker with a single GMPE, the given IMTs and one level every
# LEVEL_STEP: the error of the gridding is geometric and does not depend
# much on the GMPE, while the cost of the calibration is proportional to
# the number of GMPEs, IMTs and levels; the maximum distance is cut to
# MAXDIST, since the cost of each site grows with the area within the
# maximum distance, while the far sources are far for all the candidates
# and the reference, so they hardly contribute to the errors
def _calib_cmaker(cmaker, imts):
    md = cmaker.maximum_distance
    return cmaker.restrict(imts, LEVEL_STEP).copy(
        gsims=dict(list(cmaker.gsims.items())[:1]),
        maximum_distance=magdepdist(zip(md.x, numpy.minimum(md.y, MAXDIST))))


def calibrate(csm, cmakers, sitecol, oq, h5=None):
    """
    Determine ps_grid_spacing and pointsource_distance by comparing the
    hazard maps of the point sources on a sample of sites with the
    reference ones. All the grid spacings are tried, each one with the
    distances from the smallest (the cheapest) up to the first within
    the tolerance; the candidate within the tolerance with the smallest
    weight is chosen. NB: the largest spacing is not always the
    cheapest, since big cells make more sites close to the sources.

    If ps_grid_spacing is a fixed value, only the pointsource_distance
    is calibrated, keeping that spacing.

    :returns: (ps_grid_spacing, pointsource_distance) or None if there
              are no point sources
    """
    # NB: with a fixed spacing the candidates are only the distances
    spacings = GRID_SPACINGS if oq.auto_grid else [oq.ps_grid_spacing]
    sgs = {sg.sources[0].grp_id: sg for sg in csm.src_groups
           if not sg.atomic and any(src.code in b'AMP' for src in sg)}
    if not sgs:
        return None
    imts = _calib_imts(oq)
    cmakers = {grp_id: _calib_cmaker(cmakers[grp_id], imts)
               for grp_id in sgs}
    maxdist = {grp_id: cmakers[grp_id].maximum_distance.y[-1]
               for grp_id in sgs}
    # a complete SiteCollection, so that the tasks receive only the sample
    sites = SiteCollection.from_(sitecol.reduce(NSITES).array)
    sites.make_complete()
    groups = {grp_id: _get_points(sg, sites, maxdist[grp_id])
              for grp_id, sg in sgs.items()}
    groups = {grp_id: pts for grp_id, pts in groups.items() if pts}
    if not groups:
        return None
    return _select_candidate(groups, cmakers, sites, oq, spacings, h5)


# compare candidates on the prepared sample and return the best parameters
def _select_candidate(groups, cmakers, sites, oq, spacings, h5):
    imtls = next(iter(cmakers.values())).imtls
    distances = ([oq.pointsource_distance['default']] if oq.psd_given
                 else PS_DISTANCES)
    logging.info('Calibrating ps_grid_spacing among %s and '
                 'pointsource_distance among %s on %d sites with one GMPE '
                 'per group', spacings, distances, len(sites))
    num_tasks = parallel.num_cores * 2
    ref = None
    rows = []  # candidates with time, weight, mean_err and p99_err
    # NB: the reference has no gridding also with a fixed spacing, since
    # the errors due to the gridding and to the pointsource_distance can
    # compensate (in SAM the error with respect to a gridded reference is
    # larger than the total error); the reference is the most expensive
    # part, so it is split in more blocks to avoid slow tasks
    blocks = {psgs: _get_blocks(groups, sites, cmakers, psgs, num_tasks * (
        4 if psgs == REFERENCE[0] else 1))
        for psgs in [REFERENCE[0]] + spacings}
    # with a fixed spacing all the distances are tried in a single round,
    # to send the blocks and wait for the slowest task only once; with
    # ps_grid_spacing=auto the distances are tried from the smallest,
    # stopping when all the spacings have a candidate within tolerance;
    # the choice is the same, since the weight grows with the distance
    rounds = [[psd] for psd in distances] if oq.auto_grid else [distances]
    pending = spacings  # spacings without a candidate within tolerance
    for psds in rounds:
        logging.info('Trying ps_grid_spacing=%s with pointsource_distance=%s',
                     pending, psds)
        # the reference rates are computed in the first round
        keys = [(psgs, psd) for psd in psds for psgs in pending] + (
            [REFERENCE] * (ref is None))
        # the keys with the same spacing are computed in the same task,
        # sharing the contexts
        bypsgs = AccumDict(accum=[])
        for key in sorted(keys):
            bypsgs[key[0]].append(key)
        # run the calibration tasks in parallel, the heaviest first
        args = [(blk, sites, cmakers[blk[0].grp_id], ks)
                for psgs, ks in bypsgs.items() for blk in blocks[psgs]]
        weights = [blk.weight * len(ks) for blk, _, _, ks in args]
        args = parallel.heaviest_first(args, weights)
        results = parallel.Starmap(calibration, args, h5=h5).reduce()
        if ref is None:
            ref = get_hmaps(results.pop(REFERENCE)['rates'], imtls, oq)
        new = list(_get_rows(results, ref, imtls, oq))
        rows.extend(new)
        pending = [row.ps_grid_spacing for row in new
                   if row.p99_err > TOLERANCE]
        if not pending:
            break
    _log_rows(rows, len(sites))
    good = [row for row in rows if row.p99_err <= TOLERANCE]
    if not good:  # the candidates close to the most precise one
        minerr = min(row.p99_err for row in rows)
        good = [row for row in rows if row.p99_err <= minerr * (1 + CLOSE)]
    best = min(good, key=lambda row: row.weight)  # the cheapest
    if best.p99_err > TOLERANCE:
        logging.warning(
            'With ps_grid_spacing=%s and pointsource_distance=%s the 99th '
            'percentile of the relative error on the hazard maps is %.1f%%',
            best.ps_grid_spacing, best.pointsource_distance,
            100 * best.p99_err)
    return best.ps_grid_spacing, best.pointsource_distance


# log the candidates, with the errors as percentages
def _log_rows(rows, nsites):
    lines = ['%5.0f %5.0f %9.1f %11.0f %10.2f %9.2f' % (
        row.ps_grid_spacing, row.pointsource_distance, row.time,
        row.weight, 100 * row.mean_err, 100 * row.p99_err) for row in rows]
    logging.info('Calibration on %d sites (relative error on the hazard '
                 'maps for sites above %s g)\n'
                 ' psgs   psd      time      weight  mean_err%%  p99_err%%'
                 '\n%s', nsites, MIN_HMAP, '\n'.join(lines))


def get_hmaps(rates, imtls, oq):
    """
    :param rates: an array of shape (N, L)
    :param imtls: a DictArray with M IMTs
    :returns: the hazard maps, an array of shape (N, M, P)
    """
    curves = to_probs(rates, oq.investigation_time).reshape(
        len(rates), len(imtls), -1)
    return compute_hmaps(curves, imtls, oq.poes or [.002105])


# yield a Candidate with spacing, distance, time, weight, mean_err and p99_err,
# where mean_err and p99_err refer to the relative error on the hazard maps
def _get_rows(results, ref, imtls, oq):
    ok = ref > MIN_HMAP
    # sorted, so that the choice among equal weights does not depend on
    # the order in which the tasks finish
    for key, result in sorted(results.items()):
        hmaps = get_hmaps(result['rates'], imtls, oq)
        # if no hazard map is relevant any candidate is good
        errs = (numpy.abs(hmaps[ok] - ref[ok]) / ref[ok] if ok.any()
                else numpy.zeros(1))
        yield Candidate(*key, result['time'], result['weight'],
                        errs.mean(), numpy.percentile(errs, 99))
