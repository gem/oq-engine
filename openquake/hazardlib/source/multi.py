# The Hazard Library
# Copyright (C) 2012-2019 GEM Foundation
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
Module :mod:`openquake.hazardlib.source.area` defines :class:`AreaSource`.
"""
import numpy
from openquake.hazardlib.source.base import ParametricSeismicSource
from openquake.hazardlib.mfd.multi_mfd import MultiMFD
from openquake.hazardlib.geo import utils, NodalPlane
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.valid import SCALEREL
from openquake.hazardlib.source.point import PointSource

F32 = numpy.float32
npd_dt = numpy.dtype([('probability', F32),
                      ('strike', F32), ('dip', F32), ('rake', F32)])
hdd_dt = numpy.dtype([('probability', F32), ('depth', F32)])
mesh_dt = numpy.dtype([('lon', F32), ('lat', F32)])


def get(arr, i):
    if hasattr(arr, '__getitem__'):
        return arr[i]
    return arr


class MultiPointSource(ParametricSeismicSource):
    """
    MultiPointSource class, used to describe point sources with different
    MFDs and the same rupture_mesh_spacing, magnitude_scaling_relationship,
    rupture_aspect_ratio, temporal_occurrence_model, upper_seismogenic_depth,
    lower_seismogenic_depth, nodal_plane_distribution, hypocenter_distribution
    """
    code = b'M'
    MODIFICATIONS = set(())
    RUPTURE_WEIGHT = 0.1

    def __init__(self, source_id, name, tectonic_region_type,
                 mfd, magnitude_scaling_relationship, rupture_aspect_ratio,
                 # point-specific parameters (excluding location)
                 upper_seismogenic_depth, lower_seismogenic_depth,
                 nodal_plane_distribution, hypocenter_distribution,
                 mesh, temporal_occurrence_model=None):
        assert len(mfd) == len(mesh), (len(mfd), len(mesh))
        rupture_mesh_spacing = None
        super().__init__(
            source_id, name, tectonic_region_type, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship,
            rupture_aspect_ratio,
            temporal_occurrence_model)
        self.upper_seismogenic_depth = upper_seismogenic_depth
        self.lower_seismogenic_depth = lower_seismogenic_depth
        self.nodal_plane_distribution = nodal_plane_distribution
        self.hypocenter_distribution = hypocenter_distribution
        self.mesh = mesh

    def __iter__(self):
        for i, (mfd, point) in enumerate(zip(self.mfd, self.mesh)):
            name = '%s:%s' % (self.source_id, i)
            ps = PointSource(
                name, name, self.tectonic_region_type,
                mfd, self.rupture_mesh_spacing,
                self.magnitude_scaling_relationship,
                get(self.rupture_aspect_ratio, i),
                self.temporal_occurrence_model,
                get(self.upper_seismogenic_depth, i),
                get(self.lower_seismogenic_depth, i),
                point,
                self.nodal_plane_distribution,
                self.hypocenter_distribution)
            ps.num_ruptures = ps.count_ruptures()
            yield ps

    def __len__(self):
        return len(self.mfd)

    def iter_ruptures(self):
        """
        Yield the ruptures of the underlying point sources
        """
        for ps in self:
            for rupture in ps.iter_ruptures():
                yield rupture

    def count_ruptures(self):
        """
        See
        :meth:`openquake.hazardlib.source.base.BaseSeismicSource.count_ruptures`
        for description of parameters and return value.
        """
        return (len(self.get_annual_occurrence_rates()) *
                len(self.nodal_plane_distribution.data) *
                len(self.hypocenter_distribution.data))

    def get_bounding_box(self, maxdist):
        """
        Bounding box containing all the point sources, enlarged by the
        maximum distance.
        """
        return utils.get_bounding_box([ps.location for ps in self], maxdist)

    @property
    def polygon(self):
        """
        The polygon containing all points
        """
        return self.mesh.get_convex_hull()

    def __toh5__(self):
        npd = [(prob, np.strike, np.dip, np.rake)
               for prob, np in self.nodal_plane_distribution.data]
        hdd = self.hypocenter_distribution.data
        points = [(p.x, p.y) for p in self.mesh]
        mfd = self.mfd.kwargs.copy()
        for k, vals in mfd.items():
            if k in ('occurRates', 'magnitudes'):
                mfd[k] = [numpy.array(lst, F32) for lst in vals]
            else:
                mfd[k] = numpy.array(vals, F32)
        dic = {'nodal_plane_distribution': numpy.array(npd, npd_dt),
               'hypocenter_distribution': numpy.array(hdd, hdd_dt),
               'mesh': numpy.array(points, mesh_dt),
               'rupture_aspect_ratio': self.rupture_aspect_ratio,
               'upper_seismogenic_depth': self.upper_seismogenic_depth,
               'lower_seismogenic_depth': self.lower_seismogenic_depth,
               self.mfd.kind: mfd}
        attrs = {'source_id': self.source_id,
                 'name': self.name,
                 'magnitude_scaling_relationship':
                 self.magnitude_scaling_relationship.__class__.__name__,
                 'tectonic_region_type': self.tectonic_region_type}
        return dic, attrs

    def __fromh5__(self, dic, attrs):
        self.source_id = attrs['source_id']
        self.name = attrs['name']
        self.tectonic_region_type = attrs['tectonic_region_type']
        self.magnitude_scaling_relationship = SCALEREL[
            attrs['magnitude_scaling_relationship']]
        npd = dic.pop('nodal_plane_distribution').value
        hdd = dic.pop('hypocenter_distribution').value
        mesh = dic.pop('mesh').value
        self.rupture_aspect_ratio = dic.pop('rupture_aspect_ratio').value
        self.lower_seismogenic_depth = dic.pop('lower_seismogenic_depth').value
        self.upper_seismogenic_depth = dic.pop('upper_seismogenic_depth').value
        [(mfd_kind, mfd)] = dic.items()
        self.nodal_plane_distribution = PMF([
            (prob, NodalPlane(strike, dip, rake))
            for prob, strike, dip, rake in npd])
        self.hypocenter_distribution = PMF(hdd)
        self.mesh = Mesh(mesh['lon'], mesh['lat'])
        kw = {k: dset.value for k, dset in mfd.items()}
        kw['size'] = len(mesh)
        kw['kind'] = mfd_kind
        self.mfd = MultiMFD(**kw)

    def geom(self):
        """
        :returns: the geometry as an array of shape (N, 3)
        """
        return numpy.array([(p.x, p.y, p.z) for p in self.mesh],
                           numpy.float32)
