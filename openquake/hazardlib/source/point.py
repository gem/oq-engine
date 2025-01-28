# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.source.point` defines :class:`PointSource`.
"""
import math
import copy
import numpy
from openquake.baselib.general import AccumDict, groupby_grid, Deduplicate
from openquake.hazardlib.geo import Point, geodetic
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.geo.surface.planar import (
    build_planar, PlanarSurface, planin_dt)
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.scalerel.point import PointMSR
from openquake.hazardlib.source.base import ParametricSeismicSource
from openquake.hazardlib.source.rupture import (
    ParametricProbabilisticRupture, PointRupture)
from openquake.hazardlib.geo.utils import get_bounding_box, angular_distance


# this is fast
def get_rupdims(areas, dip, width, rar):
    """
    Calculate and return the rupture length and width
    for given magnitude surface parameters.

    :returns:
        array of shape (M, 3) with rupture lengths, widths and heights

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
    out = numpy.zeros((len(areas), 3))
    rup_length = numpy.sqrt(areas * rar)
    rup_width = areas / rup_length
    rdip = math.radians(dip)
    max_width = width / math.sin(rdip)
    big = rup_width > max_width
    rup_width[big] = max_width
    rup_length[big] = areas[big] / rup_width[big]
    out[:, 0] = rup_length
    out[:, 1] = rup_width * math.cos(rdip)
    out[:, 2] = rup_width * math.sin(rdip)
    return out


def msr_name(src):
    """
    :returns: string representation of the MSR or "Undefined" if not applicable
    """
    # NB: the MSR is None for characteristicFault sources
    try:
        return str(src.magnitude_scaling_relationship)
    except AttributeError:   # no MSR for nonparametric sources
        return 'Undefined'


def calc_average(pointsources):
    """
    :returns:
        a dict with average strike, dip, rake, lon, lat, dep,
        upper_seismogenic_depth, lower_seismogenic_depth
    """
    acc = dict(lon=[], lat=[], dep=[], strike=[], dip=[], rake=[],
               upper_seismogenic_depth=[], lower_seismogenic_depth=[],
               rupture_aspect_ratio=[])
    rates = []
    trt = pointsources[0].tectonic_region_type
    for src in pointsources:
        assert src.tectonic_region_type == trt
        rates.append(sum(r for m, r in src.get_annual_occurrence_rates()))
        ws, ds = zip(*src.nodal_plane_distribution.data)
        strike = numpy.average([np.strike for np in ds], weights=ws)
        dip = numpy.average([np.dip for np in ds], weights=ws)
        rake = numpy.average([np.rake for np in ds], weights=ws)
        ws, deps = zip(*src.hypocenter_distribution.data)
        dep = numpy.average(deps, weights=ws)
        acc['lon'].append(src.location.x)
        acc['lat'].append(src.location.y)
        acc['dep'].append(dep)
        acc['strike'].append(strike)
        acc['dip'].append(dip)
        acc['rake'].append(rake)
        acc['upper_seismogenic_depth'].append(src.upper_seismogenic_depth)
        acc['lower_seismogenic_depth'].append(src.lower_seismogenic_depth)
        acc['rupture_aspect_ratio'].append(src.rupture_aspect_ratio)
    dic = {key: numpy.average(acc[key], weights=rates) for key in acc}
    dic['lon'] = numpy.round(dic['lon'], 6)
    dic['lat'] = numpy.round(dic['lat'], 6)
    return dic


class PointSource(ParametricSeismicSource):
    """
    Point source typology represents seismicity on a single geographical
    location.

    :param upper_seismogenic_depth:
        Minimum depth an earthquake rupture can reach, in km.
    :param lower_seismogenic_depth:
        Maximum depth an earthquake rupture can reach, in km.
    :param location:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of the seismic source.
    :param nodal_plane_distribution:
        :class:`~openquake.hazardlib.pmf.PMF` object with values
        that are instances
        of :class:`openquake.hazardlib.geo.nodalplane.NodalPlane`.
        Shows the distribution
        of probability for rupture to have the certain nodal plane.
    :param hypocenter_distribution:
        :class:`~openquake.hazardlib.pmf.PMF` with values being float
        numbers in km representing the depth of the hypocenter. Latitude
        and longitude of the hypocenter is always set to ones of ``location``.

    See also :class:`openquake.hazardlib.source.base.ParametricSeismicSource`
    for description of other parameters.

    :raises ValueError:
        If upper seismogenic depth is below lower seismogenic
        depth,  if one or more of hypocenter depth values is shallower
        than upper seismogenic depth or deeper than lower seismogenic depth.
    """
    code = b'P'
    MODIFICATIONS = set()
    ps_grid_spacing = 0  # updated in CollapsedPointSource

    def __init__(self, source_id, name, tectonic_region_type,
                 mfd, rupture_mesh_spacing,
                 magnitude_scaling_relationship, rupture_aspect_ratio,
                 temporal_occurrence_model,
                 # point-specific parameters
                 upper_seismogenic_depth, lower_seismogenic_depth,
                 location, nodal_plane_distribution, hypocenter_distribution):
        super().__init__(
            source_id, name, tectonic_region_type, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio,
            temporal_occurrence_model)

        if not lower_seismogenic_depth > upper_seismogenic_depth:
            raise ValueError('lower seismogenic depth must be below '
                             'upper seismogenic depth')

        if not all(upper_seismogenic_depth <= depth <= lower_seismogenic_depth
                   for (prob, depth) in hypocenter_distribution.data):
            raise ValueError('depths of all hypocenters must be in between '
                             'lower and upper seismogenic depths')

        if not upper_seismogenic_depth > geodetic.EARTH_ELEVATION:
            raise ValueError(
                "Upper seismogenic depth must be greater than the "
                "maximum elevation on Earth's surface (-8.848 km)")

        self.location = location
        self.nodal_plane_distribution = nodal_plane_distribution
        self.hypocenter_distribution = hypocenter_distribution
        self.upper_seismogenic_depth = upper_seismogenic_depth
        self.lower_seismogenic_depth = lower_seismogenic_depth

    def restrict(self, nodalplane, depth):
        """
        :returns: source restricted to a single nodal plane and depth
        """
        new = copy.copy(self)
        new.nodal_plane_distribution = PMF([(1., nodalplane)])
        new.hypocenter_distribution = PMF([(1., depth)])
        return new

    def get_planin(self, magd, npd):
        """
        :return: array of dtype planin_dt of shape (#mags, #planes, #depths)
        """
        msr = self.magnitude_scaling_relationship
        width = self.lower_seismogenic_depth - self.upper_seismogenic_depth
        rar = self.rupture_aspect_ratio
        planin = numpy.zeros((len(magd), len(npd)), planin_dt).view(
            numpy.recarray)
        mrate, mags = numpy.array(magd).T  # shape (2, M)
        nrate = numpy.array([nrate for nrate, np in npd])
        planin['rate'] = mrate[:, None] * nrate
        for n, (nrate, np) in enumerate(npd):
            arr = planin[:, n]
            areas = msr.get_median_area(mags, np.rake)
            arr['mag'] = mags
            arr['strike'] = np.strike
            arr['dip'] = np.dip
            arr['rake'] = np.rake
            arr['dims'] = get_rupdims(areas, np.dip, width, rar)
        return planin

    def max_radius(self, maxdist):
        """
        :returns: max radius + ps_grid_spacing * sqrt(2)/2
        """
        self._get_max_rupture_projection_radius()
        eff_radius = min(self.radius[-1], maxdist / 2)
        return eff_radius + self.ps_grid_spacing * .707

    def get_psdist(self, m, mag, psdist, magdist):
        """
        :returns: the effective pointsource distance for the given magnitude
        """
        eff_radius = min(self.radius[m], magdist[mag] / 2)
        return eff_radius + self.ps_grid_spacing * .707 + psdist

    def _get_max_rupture_projection_radius(self):
        """
        Find a maximum radius of a circle on Earth surface enveloping a rupture
        produced by this source.

        :returns:
            Half of maximum rupture's diagonal surface projection.
        """
        if hasattr(self, 'radius'):
            return self.radius[-1]  # max radius
        if isinstance(self.magnitude_scaling_relationship, PointMSR):
            M = len(self.get_annual_occurrence_rates())
            self.radius = numpy.zeros(M)
            return self.radius[-1]
        magd = [(r, mag) for mag, r in self.get_annual_occurrence_rates()]
        npd = self.nodal_plane_distribution.data
        self.radius = numpy.zeros(len(magd))
        for m, planin in enumerate(self.get_planin(magd, npd)):
            rup_length, rup_width, _ = planin.dims.max(axis=0)  # (N, 3) => 3
            # the projection radius is half of the rupture diagonal
            self.radius[m] = math.sqrt(rup_length ** 2 + rup_width ** 2) / 2.0
        return self.radius[-1]  # max radius

    def get_planar(self, shift_hypo=False, iruptures=False):
        """
        :returns: a dictionary mag -> list of arrays of shape (U, 3)
        """
        magd = [(r, mag) for mag, r in self.get_annual_occurrence_rates()]
        if isinstance(self, CollapsedPointSource) and not iruptures:
            out = AccumDict(accum=[])
            for src in self.pointsources:
                out += src.get_planar(shift_hypo)
            return out

        npd = self.nodal_plane_distribution.data
        hdd = numpy.array(self.hypocenter_distribution.data)
        clon, clat = self.location.x, self.location.y
        usd = self.upper_seismogenic_depth
        lsd = self.lower_seismogenic_depth
        planin = self.get_planin(magd, npd)
        planar = build_planar(planin, hdd, clon, clat, usd, lsd)  # MND3
        if not shift_hypo:  # use the original hypocenter
            planar.hypo[:, :, :, 0] = clon
            planar.hypo[:, :, :, 1] = clat
            for d, (drate, dep) in enumerate(hdd):
                planar.hypo[:, :, d, 2] = dep
        dic = {mag: [pla.reshape(-1, 3)]
               for (_rate, mag), pla in zip(magd, planar)}
        return dic

    def _gen_ruptures(self, shift_hypo=False, step=1, iruptures=False):
        magd = [(r, mag) for mag, r in self.get_annual_occurrence_rates()]
        npd = self.nodal_plane_distribution.data
        hdd = self.hypocenter_distribution.data
        clon, clat = self.location.x, self.location.y
        if step == 1:
            # return full ruptures (one per magnitude)
            planardict = self.get_planar(shift_hypo, iruptures)
            for mag, [planar] in planardict.items():
                for pla in planar.reshape(-1, 3):
                    surface = PlanarSurface.from_(pla)
                    _strike, _dip, rake = pla.sdr
                    rate = pla.wlr[2]
                    yield ParametricProbabilisticRupture(
                        mag, rake, self.tectonic_region_type,
                        Point(*pla.hypo), surface, rate,
                        self.temporal_occurrence_model)
        else:
            # return point ruptures (fast)
            magd_ = list(enumerate(magd))
            npd_ = list(enumerate(npd))
            hdd_ = list(enumerate(hdd))
            for m, (mrate, mag) in magd_[-1:]:
                for n, (nrate, np) in npd_:
                    for d, (drate, cdep) in hdd_:
                        rate = mrate * nrate * drate
                        yield PointRupture(
                            mag, self.tectonic_region_type,
                            Point(clon, clat, cdep), rate,
                            self.temporal_occurrence_model,
                            self.lower_seismogenic_depth)

    def iter_ruptures(self, **kwargs):
        """
        Generate one rupture for each combination of magnitude, nodal plane
        and hypocenter depth.
        """
        return self._gen_ruptures(
            shift_hypo=kwargs.get('shift_hypo'),
            step=kwargs.get('step', 1))

    # PointSource
    def iruptures(self):
        """
        Generate one rupture for each magnitude, called only if nphc > 1
        """
        avg = calc_average([self])  # over nodal planes and hypocenters
        np = NodalPlane(avg['strike'], avg['dip'], avg['rake'])
        yield from self.restrict(np, avg['dep'])._gen_ruptures(iruptures=True)

    def count_nphc(self):
        """
        :returns: the number of nodal planes times the number of hypocenters
        """
        return len(self.nodal_plane_distribution.data) * len(
            self.hypocenter_distribution.data)

    def count_ruptures(self):
        """
        See :meth:
        `openquake.hazardlib.source.base.BaseSeismicSource.count_ruptures`.
        """
        return len(self.get_annual_occurrence_rates()) * self.count_nphc()

    @property
    def polygon(self):
        """
        Polygon corresponding to the max_rupture_projection_radius
        """
        radius = self._get_max_rupture_projection_radius()
        return self.location.to_polygon(radius)

    def get_bounding_box(self, maxdist):
        """
        Bounding box of the point, enlarged by the maximum distance
        """
        radius = self.max_radius(maxdist)
        return get_bounding_box([self.location], maxdist + radius)

    def wkt(self):
        """
        :returns: the geometry as a WKT string
        """
        loc = self.location
        return 'POINT(%s %s)' % (loc.x, loc.y)


def psources_to_pdata(pointsources, name):
    """
    Build a pdata dictionary from a list of homogeneous point sources
    with the same tom, trt, msr.
    """
    ps = pointsources[0]
    dt = [(f, numpy.float32) for f in 'lon lat rar usd lsd'.split()]
    array = numpy.empty(len(pointsources), dt)
    for i, ps in enumerate(pointsources):
        rec = array[i]
        loc = ps.location
        rec['lon'] = loc.x
        rec['lat'] = loc.y
        rec['rar'] = ps.rupture_aspect_ratio
        rec['usd'] = ps.upper_seismogenic_depth
        rec['lsd'] = ps.lower_seismogenic_depth
    pdata = dict(name=name,
                 array=array,
                 tom=ps.temporal_occurrence_model,
                 trt=ps.tectonic_region_type,
                 rms=ps.rupture_mesh_spacing,
                 npd=Deduplicate([ps.nodal_plane_distribution
                                  for ps in pointsources]),
                 hcd=Deduplicate([ps.hypocenter_distribution
                                  for ps in pointsources]),
                 mfd=Deduplicate([ps.mfd for ps in pointsources]),
                 msr=Deduplicate([ps.magnitude_scaling_relationship
                                  for ps in pointsources]))
    return pdata


def pdata_to_psources(pdata):
    """
    Generate point sources from a pdata dictionary
    """
    name = pdata['name']
    tom = pdata['tom']
    trt = pdata['trt']
    npd = pdata['npd']
    hcd = pdata['hcd']
    rms = pdata['rms']
    mfd = pdata['mfd']
    msr = pdata['msr']
    out = []
    for i, rec in enumerate(pdata['array']):
        out.append(PointSource(
            source_id=f'{name}:{i}',
            name=name,
            tectonic_region_type=trt,
            mfd=mfd[i],
            rupture_mesh_spacing=rms,
            magnitude_scaling_relationship=msr[i],
            rupture_aspect_ratio=rec['rar'],
            upper_seismogenic_depth=rec['usd'],
            lower_seismogenic_depth=rec['lsd'],
            location=Point(rec['lon'], rec['lat']),
            nodal_plane_distribution=npd[i],
            hypocenter_distribution=hcd[i],
            temporal_occurrence_model=tom))
    return out


class CollapsedPointSource(PointSource):
    """
    Source typology representing a cluster of point sources around a
    specific location. The underlying sources must all have the same
    tectonic region type, magnitude_scaling_relationship and
    temporal_occurrence_model.
    """
    code = b'p'
    MODIFICATIONS = set()

    def __init__(self, source_id, pointsources):
        self.source_id = source_id
        self.pdata = psources_to_pdata(pointsources, source_id)
        self.tectonic_region_type = pointsources[0].tectonic_region_type
        self.magnitude_scaling_relationship = (
            pointsources[0].magnitude_scaling_relationship)
        self.temporal_occurrence_model = (
            pointsources[0].temporal_occurrence_model)
        vars(self).update(calc_average(pointsources))
        self.location = Point(self.lon, self.lat, self.dep)
        self.nodal_plane_distribution = PMF(
            [(1., NodalPlane(self.strike, self.dip, self.rake))])
        self.hypocenter_distribution = PMF([(1., self.dep)])

    @property
    def pointsources(self):
        """
        :returns: the underlying point sources
        """
        return pdata_to_psources(self.pdata)

    def get_annual_occurrence_rates(self):
        """
        :returns: a list of pairs [(mag, mag_occur_rate), ...]
        """
        acc = AccumDict(accum=0)
        for psource in self.pointsources:
            acc += dict(psource.get_annual_occurrence_rates())
        return sorted(acc.items())

    def count_nphc(self):
        """
        :returns: the total number of nodal planes and hypocenters
        """
        return sum(src.count_nphc() for src in self.pointsources)

    def iter_ruptures(self, **kwargs):
        """
        :returns: an iterator over the underlying ruptures
        """
        step = kwargs.get('step', 1)
        for src in self.pointsources[::-step]:
            yield from src.iter_ruptures(**kwargs)

    # CollapsedPointSource
    def iruptures(self):
        """
        :yields: the underlying ruptures with mean nodal plane and hypocenter
        """
        np = NodalPlane(self.strike, self.dip, self.rake)
        yield from self.restrict(np, self.location.z)._gen_ruptures(
            iruptures=True)

    def count_ruptures(self):
        """
        :returns: the total number of underlying ruptures
        """
        return sum(src.count_ruptures()
                   for src in pdata_to_psources(self.pdata))


def grid_point_sources(sources, ps_grid_spacing):
    """
    :param sources:
        a list of sources with the same grp_id (point sources and not)
    :param ps_grid_spacing:
        value of the point source grid spacing in km; if None, do nothing
    :returns:
        a dict grp_id -> list of non-point sources and collapsed point sources
    """
    grp_id = sources[0].grp_id
    for src in sources[1:]:
        assert src.grp_id == grp_id, (src.grp_id, grp_id)
    if not ps_grid_spacing:
        return sources
    out = [src for src in sources if not hasattr(src, 'location')]
    ps = numpy.array([src for src in sources if hasattr(src, 'location')])
    if len(ps) < 2:  # nothing to collapse
        return out + list(ps)
    coords = numpy.zeros((len(ps), 3))
    for p, psource in enumerate(ps):
        coords[p, 0] = psource.location.x
        coords[p, 1] = psource.location.y
        coords[p, 2] = psource.location.z
    if (len(numpy.unique(coords[:, 0])) == 1 or
            len(numpy.unique(coords[:, 1])) == 1):
        # degenerated rectangle, there is no grid, do not collapse
        return out + list(ps)
    deltax = angular_distance(ps_grid_spacing, lat=coords[:, 1].mean())
    deltay = angular_distance(ps_grid_spacing)
    grid = groupby_grid(coords[:, 0], coords[:, 1], deltax, deltay)
    cnt = 0
    for idxs in grid.values():
        if len(idxs) > 1:
            cnt += 1
            name = 'cps-%03d-%04d' % (grp_id, cnt)
            cps = CollapsedPointSource(name, ps[idxs])
            cps.grp_id = ps[0].grp_id
            cps.trt_smr = ps[0].trt_smr
            cps.ps_grid_spacing = ps_grid_spacing
            out.append(cps)
        else:  # there is a single source
            out.append(ps[idxs[0]])
    return out


def get_rup_maxlen(src):
    """
    :returns: the maximum rupture length for point sources and area sources
    """
    if hasattr(src, 'nodal_plane_distribution'):
        maxmag, _rate = src.get_annual_occurrence_rates()[-1]
        width = src.lower_seismogenic_depth - src.upper_seismogenic_depth
        msr = src.magnitude_scaling_relationship
        rar = src.rupture_aspect_ratio
        lens = []
        for _, np in src.nodal_plane_distribution.data:
            area = msr.get_median_area(maxmag, np.rake)
            dims = get_rupdims(numpy.array([area]), np.dip, width, rar)[0]
            lens.append(dims[0])
        return max(lens)
    return 0.
