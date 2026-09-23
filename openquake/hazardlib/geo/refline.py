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
# OpenQuake is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Reference-line builders for multi-section PFD ruptures.

A ``multiFaultSource`` rupture is a set of section traces; each PFD model
declares (via ``MULTIFAULT_REFERENCE_LINE``) how ``r`` and ``x/L`` must be
measured on it:

- ``segments``: the raw segmentation (no gap bridging) - see
  :meth:`openquake.hazardlib.geo.surface.multi.MultiSurface.get_x_l_ratio`;
- ``ecs``: a smoothed representative line (penalized thin-plate spline),
  ports oq-pfdha's ``ecs_from_traces``;
- ``lcp``: a least-cost path over a fault/background cost raster, ports
  oq-pfdha's ``lcp_from_traces``.

This module implements the forward (source-model) path of oq-pfdha's
``calc/utils/{ecs,lcp}.py``: the builders consume only the section top-edge
traces, and the resulting line provides both ``r`` (distance to it) and
``x/L`` (GC2 along it). The displacement-data path of the ECS (field
observations) is not needed by the hazard and is not ported.
"""
import numpy as np
import pyproj
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.multiline import MultiLine
from openquake.hazardlib.geo.utils import OrthographicProjection

# GC2 end-extension (m) and ECS parameters, verbatim from oq-pfdha
GC2_EXT_LEN = 50000.0
LAMBDA_P = 0.05
ABS_WT_RUP = 0.05
R_THRES_MAX = 1e4
TP_K = 10
COST_FAULT = 1.0
COST_BACKGROUND = 100.0
PIXEL_SIZE_M = 100.0


# ---------------------------------------------------------------------------
# UTM projection (pyproj), matching oq-pfdha's longlat2UTM
# ---------------------------------------------------------------------------
def longlat2utm_zone(lon_mean):
    """UTM zone from the mean longitude."""
    return int((np.floor((lon_mean + 180.0) / 6.0) % 60) + 1)


class Utm(object):
    """A fixed WGS84 <-> UTM projection."""

    def __init__(self, zone):
        self.zone = zone
        crs = f'+proj=utm +zone={zone} +datum=WGS84 +units=m +no_defs'
        wgs = '+proj=longlat +datum=WGS84 +no_defs'
        self._fwd = pyproj.Transformer.from_crs(wgs, crs, always_xy=True)
        self._inv = pyproj.Transformer.from_crs(crs, wgs, always_xy=True)

    def to_xy(self, lon, lat):
        x, y = self._fwd.transform(np.asarray(lon), np.asarray(lat))
        return np.asarray(x), np.asarray(y)

    def to_lonlat(self, x, y):
        lon, lat = self._inv.transform(np.asarray(x), np.asarray(y))
        return np.asarray(lon), np.asarray(lat)


def utm_for(lon, lat, zone=None):
    """Build the UTM projection for a set of points (zone from mean lon)."""
    if zone is None:
        zone = longlat2utm_zone(float(np.mean(np.asarray(lon))))
    return Utm(zone)


# ---------------------------------------------------------------------------
# Geometry helpers (ports of ecs_functions.R rup_length / rup_avg_strike)
# ---------------------------------------------------------------------------
def rup_length_xy(x, y):
    """Polyline length in projected (m) coordinates."""
    dx = np.diff(x)
    dy = np.diff(y)
    return float(np.sum(np.sqrt(dx * dx + dy * dy)))


def rup_avg_strike_xy(x, y):
    """Length-weighted mean strike (rad, mod pi); vertices sorted by node."""
    dx = np.diff(x)
    dy = np.diff(y)
    seg_len = np.sqrt(dx * dx + dy * dy)
    ang = np.mod(np.arctan2(dy, dx), np.pi)
    return float(np.average(ang, weights=seg_len))


def _d2_central(u, f):
    """Central 2nd derivative on a non-uniform grid (R lag-2 difference)."""
    d2f = np.diff(f[1:]) - np.diff(f[:-1])
    du2 = ((u[2:] - u[:-2]) / 2.0) ** 2
    inner = d2f / du2
    return np.concatenate([[inner[0]], inner, [np.nan]])


def compute_curvature(u, x, y):
    """Curvature magnitude sqrt((x'')^2 + (y'')^2)."""
    return np.sqrt(_d2_central(u, x) ** 2 + _d2_central(u, y) ** 2)


# ---------------------------------------------------------------------------
# GC2 (u, t) via the engine MultiLine, with the 50 km end-extension
# ---------------------------------------------------------------------------
def _extend_lonlat(lon, lat, utm, ext_len=GC2_EXT_LEN):
    x, y = utm.to_xy(lon, lat)
    nx, ny = np.diff(x), np.diff(y)
    seg = np.sqrt(nx * nx + ny * ny)
    u0x, u0y = nx[0] / seg[0], ny[0] / seg[0]
    u1x, u1y = nx[-1] / seg[-1], ny[-1] / seg[-1]
    x_ext = np.concatenate([[x[0] - ext_len * u0x], x, [x[-1] + ext_len * u1x]])
    y_ext = np.concatenate([[y[0] - ext_len * u0y], y, [y[-1] + ext_len * u1y]])
    return utm.to_lonlat(x_ext, y_ext)


def gc2ext_ut(query_lon, query_lat, line_lon, line_lat, utm,
              ext_len=GC2_EXT_LEN):
    """
    GC2 ``(u, t)`` of query points w.r.t. a reference line, in km.

    The line is extended by ``ext_len`` m past each end and ``u`` is
    re-anchored so the first original vertex sits at ``u = 0``.
    """
    query_lon = np.array(np.atleast_1d(query_lon), dtype=float)
    query_lat = np.array(np.atleast_1d(query_lat), dtype=float)
    lon_ext, lat_ext = _extend_lonlat(line_lon, line_lat, utm, ext_len)
    ml = MultiLine([Line.from_vectors(lon_ext, lat_ext)])
    t_q, u_q = ml.get_tu(query_lon, query_lat)
    _t0, u0 = ml.get_tu(np.array([line_lon[0]]), np.array([line_lat[0]]))
    return np.asarray(u_q) - float(u0[0]), np.asarray(t_q)


def _dist_to_polyline_km(q_lon, q_lat, t_lon, t_lat):
    """Min distance (km) from sites to one lon/lat polyline in a local frame."""
    lon0 = float(t_lon[0])
    lat0 = float(np.mean(t_lat))
    proj = OrthographicProjection(lon0, lon0, lat0, lat0)
    tx, ty = proj(np.asarray(t_lon, float), np.asarray(t_lat, float))
    qx, qy = proj(np.asarray(q_lon, float), np.asarray(q_lat, float))
    ax, ay = tx[:-1], ty[:-1]
    bx, by = tx[1:], ty[1:]
    dx, dy = bx - ax, by - ay
    den = dx * dx + dy * dy
    apx = qx[:, None] - ax[None, :]
    apy = qy[:, None] - ay[None, :]
    with np.errstate(invalid='ignore', divide='ignore'):
        t = (apx * dx[None, :] + apy * dy[None, :]) / den[None, :]
    t = np.where(den[None, :] > 0.0, np.clip(t, 0.0, 1.0), 0.0)
    ex = apx - t * dx[None, :]
    ey = apy - t * dy[None, :]
    return np.sqrt((ex * ex + ey * ey).min(axis=1))


# ---------------------------------------------------------------------------
# ECS: penalized thin-plate spline representative line
# ---------------------------------------------------------------------------
def _tprs(u_knots, k=TP_K):
    """Thin-plate regression spline basis (Wood 2003, d=1, m=2)."""
    shift = float(np.mean(u_knots))
    kn = np.unique(u_knots) - shift
    k = int(min(k, len(kn)))
    nwig = max(k - 2, 0)
    ek = np.abs(kn[:, None] - kn[None, :]) ** 3
    tk = np.column_stack([np.ones_like(kn), kn])
    q, _ = np.linalg.qr(tk, mode='complete')
    z = q[:, 2:]
    if nwig > 0:
        w, v = np.linalg.eigh(z.T @ ek @ z)
        order = np.argsort(-np.abs(w))[:nwig]
        uk = z @ v[:, order]
        dk = np.abs(w[order])
    else:
        uk = np.zeros((len(kn), 0))
        dk = np.zeros(0)

    def evalfn(u):
        uu = np.asarray(u, dtype=float) - shift
        e = np.abs(uu[:, None] - kn[None, :]) ** 3
        return np.column_stack([e @ uk, np.ones_like(uu), uu])

    s = np.zeros((k, k))
    if nwig > 0:
        s[:nwig, :nwig] = np.diag(dk)
    return evalfn, s, shift


def fit_spline_xy(u, x, y, sp, k=TP_K):
    """Penalized fit of (x, y) ~ s(u); returns ``predict(u) -> (x, y)``."""
    u = np.asarray(u, float)
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    evalfn, s, _shift = _tprs(u, k)
    b = evalfn(u)
    k = b.shape[1]
    btb = b.T @ b
    reg = 1e-10 * np.trace(btb) / k
    low = np.linalg.cholesky(btb + reg * np.eye(k))
    lowi = np.linalg.inv(low)
    val, vec = np.linalg.eigh(lowi @ s @ lowi.T)
    t = lowi.T @ vec
    bn = b @ t
    val = np.clip(val, 0.0, None)
    vmax = val.max() if val.size else 0.0
    nz = val[val > 1e-6 * vmax] if vmax > 0 else val[:0]
    if nz.size:
        fac = np.mean(np.abs(bn.T @ bn)) / np.mean(np.abs(nz))
        a = bn.T @ bn + sp * fac * np.diag(val)
    else:
        a = bn.T @ bn
    beta_n = np.column_stack([np.linalg.solve(a, bn.T @ x),
                              np.linalg.solve(a, bn.T @ y)])
    beta = t @ beta_n

    def predict(u_new):
        xy = evalfn(u_new) @ beta
        return xy[:, 0], xy[:, 1]

    return predict, beta


def _pca_strike(x, y, wt):
    xy = np.column_stack([x, y]) * wt[:, None]
    xy = xy - xy.mean(axis=0)
    _, _, vt = np.linalg.svd(xy, full_matrices=False)
    return float(-np.arctan2(vt[0, 1], vt[0, 0]))


def _mrs_strike(traces, utm):
    """Rotation = -(length^2 weighted mean rupture strike)."""
    angs, lens = [], []
    for lon, lat in traces:
        u = utm_for(lon, lat)
        x, y = u.to_xy(lon, lat)
        angs.append(rup_avg_strike_xy(x, y))
        lens.append(rup_length_xy(x, y))
    angs = np.asarray(angs)
    lens = np.asarray(lens)
    return -float(np.average(angs, weights=lens ** 2))


def _initial_ecs(x, y, rot_th, n_pt=10):
    c, s = np.cos(rot_th), np.sin(rot_th)
    rot = np.array([[c, -s], [s, c]])
    ut = (rot @ np.column_stack([x, y]).T).T
    u_lin = np.linspace(ut[:, 0].min(), ut[:, 0].max(), n_pt)
    ecs_ut = np.column_stack([u_lin, np.zeros(n_pt)])
    ecs_xy = np.linalg.solve(rot, ecs_ut.T).T
    return ecs_xy[:, 0], ecs_xy[:, 1]


def ecs_main(lon, lat, rup_traces, lambda_p=LAMBDA_P, ecs_du=100.0,
             flt_max_ds=50.0, max_iter=50):
    """
    Construct the ECS representative line from weighted points.

    :param lon, lat: replicated data points (the weighted section vertices)
    :param rup_traces: the per-rupture traces used for the MRS start
    """
    lon = np.asarray(lon, float)
    lat = np.asarray(lat, float)
    utm = utm_for(lon, lat)
    x, y = utm.to_xy(lon, lat)
    ox, oy = x.mean(), y.mean()
    x, y = x - ox, y - oy
    rot = _mrs_strike(rup_traces, utm)
    ex, ey = _initial_ecs(x, y, rot)
    elon, elat = utm.to_lonlat(ex + ox, ey + oy)
    u_km, t_km = gc2ext_ut(lon, lat, elon, elat, utm)
    u, t = u_km * 1000.0, t_km * 1000.0
    n_iter = 0
    flt_ds = np.inf
    ecs_u = np.zeros(0)
    for n_iter in range(1, max_iter + 1):
        fault_len = float(u.max() - u.min())
        sp = lambda_p / fault_len
        predict, _beta = fit_spline_xy(u, x, y, sp)
        u0 = np.round(u.min() / ecs_du) * ecs_du
        u1 = np.round(u.max() / ecs_du) * ecs_du
        ecs_u = np.arange(u0, u1 + 0.5 * ecs_du, ecs_du)
        ex, ey = predict(ecs_u)
        elon, elat = utm.to_lonlat(ex + ox, ey + oy)
        u_km, t_km = gc2ext_ut(lon, lat, elon, elat, utm)
        un, tn = u_km * 1000.0, t_km * 1000.0
        flt_ds = float(np.mean(np.sqrt((un - u) ** 2 + (tn - t) ** 2)))
        u, t = un, tn
        if flt_ds < flt_max_ds:
            break
    return EcsResult(elon, elat, ecs_u, utm, n_iter, flt_ds)


def ecs_from_traces(traces, lambda_p=LAMBDA_P, ecs_du=100.0, flt_max_ds=50.0):
    """Build an ECS reference line from a rupture's section top-edge traces."""
    traces = [(np.asarray(lo, float), np.asarray(la, float))
              for lo, la in traces]
    traces = [(lo, la) for lo, la in traces if len(lo) >= 2]
    if len(traces) < 1:
        raise ValueError('ecs_from_traces needs >=1 trace with >=2 vertices')
    # forward weighting: each vertex carries abs_wt_rup * (rupture_len / n)
    wt_lon, wt_lat, wt = [], [], []
    for lon, lat in traces:
        u = utm_for(lon, lat)
        x, y = u.to_xy(lon, lat)
        seg_len = rup_length_xy(x, y)
        wt_lon.append(lon)
        wt_lat.append(lat)
        wt.append(np.full(len(lon), ABS_WT_RUP * seg_len / len(lon)))
    wt = np.concatenate(wt)
    min_wt = float(np.min(wt))
    n_rep = np.clip(np.round(wt / min_wt), 1, R_THRES_MAX).astype(int)
    lon = np.repeat(np.concatenate(wt_lon), n_rep)
    lat = np.repeat(np.concatenate(wt_lat), n_rep)
    return ecs_main(lon, lat, traces, lambda_p, ecs_du, flt_max_ds)


# ---------------------------------------------------------------------------
# LCP: least-cost path over a fault/background cost raster
# ---------------------------------------------------------------------------
class GeoTransform(object):
    """GDAL-style north-up geotransform (corner-anchored)."""

    def __init__(self, origin_x, origin_y, pixel_dx, pixel_dy):
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.pixel_dx = pixel_dx
        self.pixel_dy = pixel_dy

    def map_to_pixel(self, x, y):
        col = int((x - self.origin_x) / self.pixel_dx)
        row = int((y - self.origin_y) / self.pixel_dy)
        return col, row

    def pixel_to_map(self, col, row):
        x = self.origin_x + np.asarray(col, float) * self.pixel_dx
        y = self.origin_y + np.asarray(row, float) * self.pixel_dy
        return x, y


def route_through_grid(cost, start_rc, stop_rc):
    """Least-cost 8-connected path across a cost grid (scipy dijkstra)."""
    cost = np.asarray(cost, dtype=float)
    nr, nc = cost.shape
    for name, (r, c) in (('start', start_rc), ('stop', stop_rc)):
        if not (0 <= r < nr and 0 <= c < nc):
            raise ValueError(f'{name} cell {(r, c)} outside {cost.shape} grid')
    n = nr * nc
    passable = np.isfinite(cost)
    idx = np.arange(n).reshape(nr, nc)
    rows_l, cols_l, wts_l = [], [], []
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        r0, r1 = max(0, -dr), min(nr, nr - dr)
        c0, c1 = max(0, -dc), min(nc, nc - dc)
        a = idx[r0:r1, c0:c1]
        b = idx[r0 + dr:r1 + dr, c0 + dc:c1 + dc]
        ok = passable[r0:r1, c0:c1] & passable[r0 + dr:r1 + dr, c0 + dc:c1 + dc]
        step = np.sqrt(float(dr * dr + dc * dc))
        w = 0.5 * (cost[r0:r1, c0:c1]
                   + cost[r0 + dr:r1 + dr, c0 + dc:c1 + dc]) * step
        rows_l.append(a[ok].ravel())
        cols_l.append(b[ok].ravel())
        wts_l.append(w[ok].ravel())
    graph = coo_matrix(
        (np.concatenate(wts_l),
         (np.concatenate(rows_l), np.concatenate(cols_l))),
        shape=(n, n)).tocsr()
    start = int(start_rc[0]) * nc + int(start_rc[1])
    stop = int(stop_rc[0]) * nc + int(stop_rc[1])
    dist, pred = dijkstra(graph, directed=False, indices=start,
                          return_predecessors=True)
    if not np.isfinite(dist[stop]):
        raise ValueError('no traversable path between start and stop cells')
    path = [stop]
    while path[-1] != start:
        path.append(int(pred[path[-1]]))
    path = np.asarray(path[::-1], dtype=int)
    return np.column_stack([path // nc, path % nc]), float(dist[stop])


def route_through_raster(cost, gt, start_xy, stop_xy):
    """LCP between two map-coordinate points across a georeferenced raster."""
    c0, r0 = gt.map_to_pixel(start_xy[0], start_xy[1])
    c1, r1 = gt.map_to_pixel(stop_xy[0], stop_xy[1])
    path_rc, total = route_through_grid(cost, (r0, c0), (r1, c1))
    x, y = gt.pixel_to_map(path_rc[:, 1], path_rc[:, 0])
    return np.column_stack([x, y]), path_rc, total


def rasterize_traces_xy(traces_xy, pixel_size, start_xy, stop_xy,
                        cost_fault=COST_FAULT, cost_background=COST_BACKGROUND):
    """Burn projected polyline traces into a cost raster."""
    allv = np.vstack([np.asarray(t, float) for t in traces_xy])
    left = min(allv[:, 0].min(), start_xy[0], stop_xy[0]) - pixel_size
    right = max(allv[:, 0].max(), start_xy[0], stop_xy[0]) + pixel_size
    bot = min(allv[:, 1].min(), start_xy[1], stop_xy[1]) - pixel_size
    top = max(allv[:, 1].max(), start_xy[1], stop_xy[1]) + pixel_size
    nc = int((right - left) / pixel_size) + 1
    nr = int((top - bot) / pixel_size) + 1
    gt = GeoTransform(left, top, pixel_size, -pixel_size)
    cost = np.full((nr, nc), cost_background, dtype=float)
    step = 0.5 * pixel_size
    for t in traces_xy:
        t = np.asarray(t, float)
        for i in range(len(t) - 1):
            seg = t[i + 1] - t[i]
            n_s = max(int(np.ceil(np.hypot(*seg) / step)), 1)
            frac = np.linspace(0.0, 1.0, n_s + 1)
            xs = t[i, 0] + frac * seg[0]
            ys = t[i, 1] + frac * seg[1]
            cols = ((xs - gt.origin_x) / gt.pixel_dx).astype(int)
            rows = ((ys - gt.origin_y) / gt.pixel_dy).astype(int)
            ok = (rows >= 0) & (rows < nr) & (cols >= 0) & (cols < nc)
            cost[rows[ok], cols[ok]] = cost_fault
    return cost, gt


def _farthest_endpoint_pair(traces_xy):
    """Start/end: the farthest-apart pair of section-trace endpoints,
    oriented along the length^2-weighted mean rupture strike."""
    ends = np.vstack([np.asarray(t, float)[[0, -1]] for t in traces_xy])
    d2 = ((ends[:, None, :] - ends[None, :, :]) ** 2).sum(axis=2)
    i, j = np.unravel_index(np.argmax(d2), d2.shape)
    a, b = ends[i], ends[j]
    angs, lens = [], []
    for t in traces_xy:
        t = np.asarray(t, float)
        angs.append(rup_avg_strike_xy(t[:, 0], t[:, 1]))
        lens.append(rup_length_xy(t[:, 0], t[:, 1]))
    strike = float(np.average(np.asarray(angs), weights=np.asarray(lens) ** 2))
    sdir = np.array([np.cos(strike), np.sin(strike)])
    if float(np.dot(b - a, sdir)) < 0.0:
        a, b = b, a
    return a, b


def _decimate_collinear(path_rc):
    """Drop interior nodes of straight pixel runs."""
    if len(path_rc) <= 2:
        return path_rc
    d = np.diff(path_rc, axis=0)
    turn = np.any(d[1:] != d[:-1], axis=1)
    keep = np.concatenate([[True], turn, [True]])
    return path_rc[keep]


def lcp_from_traces(traces, pixel_size=PIXEL_SIZE_M, cost_fault=COST_FAULT,
                    cost_background=COST_BACKGROUND, smooth=False):
    """Build an LCP reference line from a rupture's section top-edge traces."""
    traces = [(np.asarray(lo, float), np.asarray(la, float))
              for lo, la in traces]
    traces = [(lo, la) for lo, la in traces if len(lo) >= 2]
    if len(traces) < 1:
        raise ValueError('lcp_from_traces needs >=1 trace with >=2 vertices')
    all_lon = np.concatenate([lo for lo, _ in traces])
    all_lat = np.concatenate([la for _, la in traces])
    utm = utm_for(all_lon, all_lat)
    traces_xy = [np.column_stack(utm.to_xy(lo, la)) for lo, la in traces]
    start_xy, stop_xy = _farthest_endpoint_pair(traces_xy)
    cost, gt = rasterize_traces_xy(traces_xy, pixel_size, start_xy, stop_xy,
                                   cost_fault, cost_background)
    _xy, path_rc, total = route_through_raster(cost, gt, start_xy, stop_xy)
    path_rc = _decimate_collinear(path_rc)
    x, y = gt.pixel_to_map(path_rc[:, 1], path_rc[:, 0])
    lon, lat = utm.to_lonlat(x, y)
    u = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(x), np.diff(y)))])
    return LcpResult(lon, lat, u, utm, total, pixel_size)


# ---------------------------------------------------------------------------
# Reference-line results
# ---------------------------------------------------------------------------
class RefLine(object):
    """A representative line exposing ``x_l`` and ``r_km``."""

    def __init__(self, lon, lat, u, utm):
        self.lon = np.asarray(lon, float)
        self.lat = np.asarray(lat, float)
        self.u = np.asarray(u, float)
        self.utm = utm

    @property
    def length_km(self):
        return float(self.u.max() - self.u.min()) / 1000.0

    def x_l(self, lon, lat):
        """``(x/L clipped to [0, 1], L_km)`` via GC2 on the line."""
        q_lon = np.atleast_1d(np.asarray(lon, float))
        u_km, _t = gc2ext_ut(q_lon, np.atleast_1d(np.asarray(lat, float)),
                             self.lon, self.lat, self.utm)
        # gc2ext_ut returns u in km (the engine MultiLine unit), while the
        # ECS/LCP self.u grid is in metres (ecs_du is metres, the LCP u is a
        # cumulative hypot in UTM metres): convert before normalising
        u_m = u_km * 1000.0
        u_min = self.u.min()
        l_m = self.u.max() - u_min
        if l_m <= 0.0:
            return np.zeros(len(q_lon)), 0.0
        return np.clip((u_m - u_min) / l_m, 0.0, 1.0), l_m / 1000.0

    def r_km(self, lon, lat):
        """Min horizontal distance (km) to the reference line."""
        return _dist_to_polyline_km(
            np.atleast_1d(np.asarray(lon, float)),
            np.atleast_1d(np.asarray(lat, float)), self.lon, self.lat)


class EcsResult(RefLine):
    """ECS reference line (smoothed representative line)."""

    def __init__(self, lon, lat, u, utm, n_iter, flt_ds):
        super().__init__(lon, lat, u, utm)
        self.n_iter = n_iter
        self.flt_ds = flt_ds


class LcpResult(RefLine):
    """LCP reference line (least-cost path)."""

    def __init__(self, lon, lat, u, utm, total_cost, pixel_size):
        super().__init__(lon, lat, u, utm)
        self.total_cost = total_cost
        self.pixel_size = pixel_size


class SegmentsResult(RefLine):
    """Raw segmentation (r = min distance to any section trace).

    Note the unit convention differs from the ECS/LCP results: the GC2
    ``MultiLine`` u (stored in ``self.u``) is in km, not metres, so both
    :attr:`length_km` and :meth:`x_l` are overridden to stay in km.
    """

    def __init__(self, traces):
        self.traces = [(np.asarray(lo, float), np.asarray(la, float))
                       for lo, la in traces]
        self.traces = [(lo, la) for lo, la in self.traces if len(lo) >= 2]
        if not self.traces:
            raise ValueError('SegmentsResult needs >=1 trace with >=2 vertices')
        lon = np.concatenate([lo for lo, _ in self.traces])
        lat = np.concatenate([la for _, la in self.traces])
        ml = MultiLine([Line.from_vectors(lo.copy(), la.copy())
                        for lo, la in self.traces])
        _t, u_v = ml.get_tu(lon.copy(), lat.copy())
        super().__init__(lon, lat, u_v, None)
        self._ml = ml
        self._u_min = float(np.min(u_v))
        self._u_max = float(np.max(u_v))

    @property
    def length_km(self):
        return self._u_max - self._u_min

    def x_l(self, lon, lat):
        q_lon = np.atleast_1d(np.asarray(lon, float))
        l_km = self.length_km
        if l_km <= 0.0:
            return np.zeros(len(q_lon)), 0.0
        _t, u = self._ml.get_tu(
            q_lon, np.atleast_1d(np.asarray(lat, float)))
        xl = np.clip((np.asarray(u) - self._u_min) / l_km, 0.0, 1.0)
        return xl, l_km

    def r_km(self, lon, lat):
        q_lon = np.atleast_1d(np.asarray(lon, float))
        q_lat = np.atleast_1d(np.asarray(lat, float))
        best = np.full(len(q_lon), np.inf)
        for t_lon, t_lat in self.traces:
            best = np.minimum(best, _dist_to_polyline_km(
                q_lon, q_lat, t_lon, t_lat))
        return best


def reference_line(traces, method):
    """
    Build the reference line for a multi-section rupture.

    :param traces: iterable of ``(lon, lat)`` section top-edge arrays
    :param method: 'segments' | 'ecs' | 'lcp'
    """
    if method == 'segments':
        return SegmentsResult(traces)
    if method == 'ecs':
        return ecs_from_traces(traces)
    if method == 'lcp':
        return lcp_from_traces(traces)
    raise ValueError(f'unknown reference-line method {method!r}')
