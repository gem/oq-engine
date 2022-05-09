# The Hazard Library
# Copyright (C) 2012-2022 GEM Foundation
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
from unittest.mock import Mock
import numpy
from openquake.baselib.general import AccumDict, groupby_grid
from openquake.baselib.performance import Monitor
from openquake.hazardlib.geo import Point, geodetic
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.source.base import (
    ParametricSeismicSource, build_planar_surfaces, surfin_dt)
from openquake.hazardlib.source.rupture import (
    ParametricProbabilisticRupture, PointRupture)
from openquake.hazardlib.geo.utils import get_bounding_box, angular_distance


def _get_rupture_dimensions(surfin):
    """
    Calculate and return the rupture length and width
    for given magnitude surface parameters.
    :returns:
        array with rupture length, rupture width, rupture height

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
    rup_length = math.sqrt(surfin.area * surfin.rar)
    rup_width = surfin.area / rup_length
    seismogenic_layer_width = surfin.lsd - surfin.usd
    rdip = math.radians(surfin.dip)
    max_width = seismogenic_layer_width / math.sin(rdip)
    if rup_width > max_width:
        rup_width = max_width
        rup_length = surfin.area / rup_width
    return numpy.array([rup_length, rup_width * math.cos(rdip),
                        rup_width * math.sin(rdip)])


def msr_name(src):
    """
    :returns: the name of MSR class or "Undefined" if not applicable
    """
    try:
        return src.magnitude_scaling_relationship.__class__.__name__
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
    msr = msr_name(pointsources[0])
    for src in pointsources:
        assert src.tectonic_region_type == trt
        assert msr_name(src) == msr
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


def _gen_ruptures(src, nplanes=(), hypos=(), shift_hypo=False, step=1):
    mags, rates = zip(*src.get_annual_occurrence_rates())
    if not nplanes:
        np_probs, nplanes = zip(*src.nodal_plane_distribution.data)
    else:
        np_probs = [1.]
    if not hypos:
        hc_probs, cdeps = zip(*src.hypocenter_distribution.data)
        clon, clat = src.location.x, src.location.y
    else:
        hc_probs, hypo = [1.], hypos[0]
        clon, clat, cdeps = hypo.x, hypo.y, [hypo.z]
    if step == 1:  # regular case, return full ruptures
        surfin = src.get_surfin(mags, nplanes)
        surfaces = build_planar_surfaces(surfin, clon, clat, cdeps, shift_hypo)
        for m, mag in enumerate(mags):
            for n, np in enumerate(nplanes):
                for d, hc_prob in enumerate(hc_probs):
                    rate = rates[m] * np_probs[n] * hc_prob
                    surface = surfaces[m, n, d]
                    rup = ParametricProbabilisticRupture(
                        mag, np.rake, src.tectonic_region_type,
                        surface.hc, surface, rate,
                        src.temporal_occurrence_model)
                    rup.m = m
                    yield rup
    else:  # in preclassical return point ruptures (fast)
        hc = Point(clon, clat, cdeps[0])
        items = list(enumerate((zip(rates, mags))))[::-step]
        for m, (mrate, mag) in items:
            np = nplanes[0]
            rate = mrate * np_probs[0] * hc_probs[0]
            rup = PointRupture(
                mags[0], src.tectonic_region_type, hc, np.strike,
                np.rake, rate, src.temporal_occurrence_model)
            rup.m = m
            yield rup


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

    def get_surfin(self, mags, nplanes):
        """
        :return: array of dtype surfin_dt of shape (num_mags, num_planes)
        """
        msr = self.magnitude_scaling_relationship
        surfin = numpy.zeros((len(mags), len(nplanes)), surfin_dt).view(
            numpy.recarray)
        for m, mag in enumerate(mags):
            for n, np in enumerate(nplanes):
                rec = surfin[m, n]
                rec['usd'] = self.upper_seismogenic_depth
                rec['lsd'] = self.lower_seismogenic_depth
                rec['rar'] = self.rupture_aspect_ratio
                rec['mag'] = mag
                rec['area'] = msr.get_median_area(mag, np.rake)
                rec['strike'] = np.strike
                rec['dip'] = np.dip
                rec['rake'] = np.rake
                rec['dims'] = _get_rupture_dimensions(rec)
        return surfin

    def _get_max_rupture_projection_radius(self, mag=None):
        """
        Find a maximum radius of a circle on Earth surface enveloping a rupture
        produced by this source.

        :returns:
            Half of maximum rupture's diagonal surface projection.
        """
        if mag is None:
            mag, _rate = self.get_annual_occurrence_rates()[-1]
        radius = []
        _, nplanes = zip(*self.nodal_plane_distribution.data)
        for surfin in self.get_surfin([mag], nplanes)[0]:
            rup_length, rup_width, _ = _get_rupture_dimensions(surfin)
            # the projection radius is half of the rupture diagonal
            radius.append(math.sqrt(rup_length ** 2 + rup_width ** 2) / 2.0)
        self.radius = max(radius)
        return self.radius

    def get_radius(self, rup, dip=90.):
        """
        :returns: half of maximum rupture's diagonal surface projection
        """
        [[surfin]] = self.get_surfin(
            [rup.mag], [NodalPlane(rup.surface.strike, dip, rup.rake)])
        rup_length, rup_width, _ = _get_rupture_dimensions(surfin)
        return math.sqrt(rup_length ** 2 + rup_width ** 2) / 2.0

    def iter_ruptures(self, **kwargs):
        """
        Generate one rupture for each combination of magnitude, nodal plane
        and hypocenter depth.
        """
        return _gen_ruptures(
            self,
            shift_hypo=kwargs.get('shift_hypo'),
            step=kwargs.get('step', 1))

    # PointSource
    def iruptures(self):
        """
        Generate one rupture for each magnitude, called only if nphc > 1
        """
        avg = calc_average([self])  # over nodal planes and hypocenters
        np = Mock(strike=avg['strike'], dip=avg['dip'], rake=avg['rake'])
        hc = Point(avg['lon'], avg['lat'], avg['dep'])
        yield from _gen_ruptures(self, [np], [hc])

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
        radius = self._get_max_rupture_projection_radius()
        return get_bounding_box([self.location], maxdist + radius)

    def wkt(self):
        """
        :returns: the geometry as a WKT string
        """
        loc = self.location
        return 'POINT(%s %s)' % (loc.x, loc.y)


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
        self.pointsources = pointsources
        self.tectonic_region_type = pointsources[0].tectonic_region_type
        self.magnitude_scaling_relationship = (
            pointsources[0].magnitude_scaling_relationship)
        self.temporal_occurrence_model = (
            pointsources[0].temporal_occurrence_model)
        vars(self).update(calc_average(pointsources))
        self.location = Point(self.lon, self.lat, self.dep)

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
        for src in self.pointsources[::step]:
            yield from src.iter_ruptures(**kwargs)

    # CollapsedPointSource
    def iruptures(self):
        """
        :yields: the underlying ruptures with mean nodal plane and hypocenter
        """
        np = NodalPlane(self.strike, self.dip, self.rake)
        yield from _gen_ruptures(self, [np], [self.location])

    def _get_max_rupture_projection_radius(self, mag=None):
        """
        Find a maximum radius of a circle on Earth surface enveloping a rupture
        produced by this source.

        :returns:
            Half of maximum rupture's diagonal surface projection.
        """
        if mag is None:
            mag, _rate = self.get_annual_occurrence_rates()[-1]
        [[surfin]] = self.get_surfin(
            [mag], [NodalPlane(self.strike, self.dip, self.rake)])
        rup_length, rup_width, _ = _get_rupture_dimensions(surfin)
        # the projection radius is half of the rupture diagonal
        self.radius = math.sqrt(rup_length ** 2 + rup_width ** 2) / 2.0
        return self.radius

    def count_ruptures(self):
        """
        :returns: the total number of underlying ruptures
        """
        return sum(src.count_ruptures() for src in self.pointsources)


def grid_point_sources(sources, ps_grid_spacing, monitor=Monitor()):
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
        return {grp_id: sources}
    out = [src for src in sources if not hasattr(src, 'location')]
    ps = numpy.array([src for src in sources if hasattr(src, 'location')])
    if len(ps) < 2:  # nothing to collapse
        return {grp_id: out + list(ps)}
    coords = numpy.zeros((len(ps), 3))
    for p, psource in enumerate(ps):
        coords[p, 0] = psource.location.x
        coords[p, 1] = psource.location.y
        coords[p, 2] = psource.location.z
    deltax = angular_distance(ps_grid_spacing, lat=coords[:, 1].mean())
    deltay = angular_distance(ps_grid_spacing)
    grid = groupby_grid(coords[:, 0], coords[:, 1], deltax, deltay)
    task_no = getattr(monitor, 'task_no', 0)
    for i, idxs in enumerate(grid.values()):
        if len(idxs) > 1:
            cps = CollapsedPointSource('cps-%d-%d' % (task_no, i), ps[idxs])
            cps.grp_id = ps[0].grp_id
            cps.trt_smr = ps[0].trt_smr
            out.append(cps)
        else:  # there is a single source
            out.append(ps[idxs[0]])
    return {grp_id: out}
