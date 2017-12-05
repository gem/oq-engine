# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
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
Package :mod:`openquake.hazardlib.source` deals with various types
of seismic sources.
"""
import copy
import math
from openquake.hazardlib import geo, mfd
from openquake.hazardlib.source.rupture import BaseRupture, \
ParametricProbabilisticRupture, NonParametricProbabilisticRupture
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.source.area import AreaSource
from openquake.hazardlib.source.simple_fault import SimpleFaultSource
from openquake.hazardlib.source.complex_fault import ComplexFaultSource
from openquake.hazardlib.source.characteristic import CharacteristicFaultSource
from openquake.hazardlib.source.non_parametric import NonParametricSeismicSource
from openquake.hazardlib.source.multi import MultiPointSource


MINWEIGHT = 200  # tuned by M. Simionato


def area_to_point_sources(area_src):
    """
    Split an area source into a generator of point sources.

    MFDs will be rescaled appropriately for the number of points in the area
    mesh.

    :param area_src:
        :class:`openquake.hazardlib.source.AreaSource`
    """
    mesh = area_src.polygon.discretize(area_src.area_discretization)
    num_points = len(mesh)
    area_mfd = area_src.mfd

    if isinstance(area_mfd, mfd.TruncatedGRMFD):
        new_mfd = mfd.TruncatedGRMFD(
            a_val=area_mfd.a_val - math.log10(num_points),
            b_val=area_mfd.b_val,
            bin_width=area_mfd.bin_width,
            min_mag=area_mfd.min_mag,
            max_mag=area_mfd.max_mag)
    elif isinstance(area_mfd, mfd.EvenlyDiscretizedMFD):
        new_occur_rates = [x / num_points for x in area_mfd.occurrence_rates]
        new_mfd = mfd.EvenlyDiscretizedMFD(
            min_mag=area_mfd.min_mag,
            bin_width=area_mfd.bin_width,
            occurrence_rates=new_occur_rates)
    elif isinstance(area_mfd, mfd.ArbitraryMFD):
        new_occur_rates = [x / num_points for x in area_mfd.occurrence_rates]
        new_mfd = mfd.ArbitraryMFD(
            magnitudes=area_mfd.magnitudes,
            occurrence_rates=new_occur_rates)
    elif isinstance(area_mfd, mfd.YoungsCoppersmith1985MFD):
        new_mfd = mfd.YoungsCoppersmith1985MFD.from_characteristic_rate(
            area_mfd.min_mag, area_mfd.b_val, area_mfd.char_mag,
            area_mfd.char_rate / num_points, area_mfd.bin_width)
    else:
        raise TypeError('Unknown MFD: %s' % area_mfd)

    for i, (lon, lat) in enumerate(zip(mesh.lons, mesh.lats)):
        pt = PointSource(
            # Generate a new ID and name
            source_id='%s:%s' % (area_src.source_id, i),
            name='%s:%s' % (area_src.name, i),
            tectonic_region_type=area_src.tectonic_region_type,
            mfd=new_mfd,
            rupture_mesh_spacing=area_src.rupture_mesh_spacing,
            magnitude_scaling_relationship=
            area_src.magnitude_scaling_relationship,
            rupture_aspect_ratio=area_src.rupture_aspect_ratio,
            upper_seismogenic_depth=area_src.upper_seismogenic_depth,
            lower_seismogenic_depth=area_src.lower_seismogenic_depth,
            location=geo.Point(lon, lat),
            nodal_plane_distribution=area_src.nodal_plane_distribution,
            hypocenter_distribution=area_src.hypocenter_distribution,
            temporal_occurrence_model=area_src.temporal_occurrence_model)
        pt.num_ruptures = pt.count_ruptures()
        yield pt


def _split_start_stop(n, chunksize):
    start = 0
    while start < n:
        stop = start + chunksize
        yield start, min(stop, n)
        start = stop


# this is only called on heavy sources
def split_fault_source(src):
    """
    Generator splitting a fault source into several fault sources.

    :param src:
        an instance of :class:`openquake.hazardlib.source.base.SeismicSource`
    """
    # NB: the splitting is tricky; if you don't split, you will not
    # take advantage of the multiple cores; if you split too much,
    # the data transfer will kill you, i.e. multiprocessing/celery
    # will fail to transmit to the workers the generated sources.
    i = 0
    splitlist = []
    mag_rates = [(mag, rate) for (mag, rate) in
                 src.mfd.get_annual_occurrence_rates() if rate]
    if len(mag_rates) > 1:  # split by magnitude bin
        for mag, rate in mag_rates:
            new_src = copy.copy(src)
            new_src.source_id = '%s:%s' % (src.source_id, i)
            new_src.mfd = mfd.ArbitraryMFD([mag], [rate])
            i += 1
            splitlist.append(new_src)
    elif hasattr(src, 'start'):  # split by slice of ruptures
        # for instance ClassicalTestCase.test_case_20
        for start, stop in _split_start_stop(src.num_ruptures, MINWEIGHT):
            new_src = copy.copy(src)
            new_src.start = start
            new_src.stop = stop
            new_src.num_ruptures = stop - start
            new_src.source_id = '%s:%s' % (src.source_id, i)
            i += 1
            splitlist.append(new_src)
    else:
        splitlist.append(src)
    return splitlist


def _split_source(src):
    # helper for split_source
    if hasattr(src, '__iter__'):  # multipoint source
        for s in src:
            yield s
    elif isinstance(src, AreaSource):
        for s in area_to_point_sources(src):
            yield s
    elif isinstance(
            src, (SimpleFaultSource, ComplexFaultSource)):
        for s in split_fault_source(src):
            yield s
    else:
        # characteristic and nonparametric sources are not split
        # since they are small anyway
        yield src

split_map = {}  # cache


def split_source(src):
    """
    :param src: a source to split
    :returns: a list of split sources
    """
    try:
        splits = split_map[src]  # read from the cache
    except KeyError:  # fill the cache
        splits = split_map[src] = list(_split_source(src))
        if len(splits) > 1:
            has_serial = hasattr(src, 'serial')
            start = 0
            for split in splits:
                split.src_group_id = src.src_group_id
                split.num_ruptures = split.count_ruptures()
                split.ngsims = src.ngsims
                if has_serial:
                    nr = split.num_ruptures
                    split.serial = src.serial[start:start + nr]
                    start += nr
    return splits
