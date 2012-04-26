# Copyright (c) 2010-2012, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.


"""Simple objects models to represent elements of NRML artifacts. These models
are intended to be produced by NRML XML parsers and consumed by NRMl XML
serializers.
"""


class SourceModel(object):
    """Simple container for source objects, plus metadata.

    :param str name:
        Name of the source model.
    :param sources:
        Iterable of seismic source objects (:class:`PointSource`,
        :class:`AreaSource`, :class:`SimpleFaultSource`,
        :class:`ComplexFaultSource`).
    """

    def __init__(self, name=None, sources=None):
        self.name = name
        self.sources = sources

    def __iter__(self):
        return self.sources

    def next(self):
        for src in self.sources:
            yield src

    def __eq__(self, other):
        return (
            self.name == other.name
            and list(self.sources) == list(other.sources)
        )


class PointSource(object):
    """Basic object representation of a Point Source.

    :param str id:
        Source identifier, unique within a given model.
    :param str name:
        Human-readable name for the source.
    :param geometry:
        :class:`PointGeometry` instance.
    :param str mag_scale_rel:
        Magnitude Scaling Relationship.
    :param float rupt_aspect_ratio:
        Rupture Aspect Ratio.
    :param mfd:
        Magnitude Frequency Distribution. An instance of
        :class:`IncrementalMFD` or :class:`TGRMFD`.
    :param list nodal_plane_dist:
        `list` of :class:`NodalPlane` objects which make up a Nodal Plane
        Distribution.
    :param list hypo_depth_dist:
        `list` of :class:`HypocentralDepth` instances which make up a
        Hypocentral Depth Distribution.
    """

    def __init__(self, id=None, name=None, geometry=None, mag_scale_rel=None,
                 rupt_aspect_ratio=None, mfd=None, nodal_plane_dist=None,
                 hypo_depth_dist=None):
        self.id = id
        self.name = name
        self.geometry = geometry
        self.mag_scale_rel = mag_scale_rel
        self.rupt_aspect_ratio = rupt_aspect_ratio
        self.mfd = mfd
        self.nodal_plane_dist = nodal_plane_dist
        self.hypo_depth_dist = hypo_depth_dist

    def __eq__(self, other):
        return (
            self.id == other.id and self.name == other.name
            and self.geometry == other.geometry
            and self.mag_scale_rel == other.mag_scale_rel
            and self.rupt_aspect_ratio == other.rupt_aspect_ratio
            and self.mfd == self.mfd
            and self.nodal_plane_dist == other.nodal_plane_dist
            and self.hypo_depth_dist == other.hypo_depth_dist
        )


class PointGeometry(object):
    """Basic object representation of a geometry for a :class:`PointSource`.

    :param str wkt:
        WKT representing the point geometry (a POINT).
    :param float upper_seismo_depth:
        Upper seismogenic depth.
    :param float lower_seismo_depth:
        Lower siesmogenic depth.
    """

    def __init__(self, wkt=None, upper_seismo_depth=None,
                 lower_seismo_depth=None):
        self.wkt = wkt
        self.upper_seismo_depth = upper_seismo_depth
        self.lower_seismo_depth = lower_seismo_depth

    def __eq__(self, other):
        return (
            self.wkt == other.wkt
            and self.upper_seismo_depth == other.upper_seismo_depth
            and self.lower_seismo_depth == other.lower_seismo_depth
        )


class AreaSource(PointSource):
    """Basic object representation of an Area Source.

    :param str id:
        Source identifier, unique within a given model.
    :param str name:
        Human-readable name for the source.
    :param geometry:
        :class:`AreaGeometry` instance.
    :param str mag_scale_rel:
        Magnitude Scaling Relationship.
    :param float rupt_aspect_ratio:
        Rupture Aspect Ratio.
    :param mfd:
        Magnitude Frequency Distribution. An instance of
        :class:`IncrementalMFD` or :class:`TGRMFD`.
    :param list nodal_plane_dist:
        `list` of :class:`NodalPlane` objects which make up a Nodal Plane
        Distribution.
    :param list hypo_depth_dist:
        `list` of :class:`HypocentralDepth` instances which make up a
        Hypocentral Depth Distribution.
    """


class AreaGeometry(PointGeometry):
    """Basic object representation of a geometry for a :class:`PointSource`.

    :param str wkt:
        WKT representing the area geometry (a POLYGON).
    :param float upper_seismo_depth:
        Upper seismogenic depth.
    :param float lower_seismo_depth:
        Lower siesmogenic depth.
    """


class SimpleFaultSource(object):
    """Basic object representation of a Simple Fault Source.

   :param str id:
        Source identifier, unique within a given model.
   :param str name:
        Human-readable name for the source.
   :param geometry:
        :class:`SimpleFaultGeometry` object.
    :param str mag_scale_rel:
        Magnitude Scaling Relationship.
    :param float rupt_aspect_ratio:
        Rupture Aspect Ratio.
    :param mfd:
        Magnitude Frequency Distribution. An instance of
        :class:`IncrementalMFD` or :class:`TGRMFD`.
    :param float rake:
        Rake angle.
    """

    def __init__(self, id=None, name=None, geometry=None, mag_scale_rel=None,
                 rupt_aspect_ratio=None, mfd=None, rake=None):
        self.id = id
        self.name = name
        self.geometry = geometry
        self.mag_scale_rel = mag_scale_rel
        self.rupt_aspect_ratio = rupt_aspect_ratio
        self.mfd = mfd
        self.rake = rake

    def __eq__(self, other):
        return (
            self.geometry == other.geometry
            and self.mag_scale_rel == other.mag_scale_rel
            and self.rupt_aspect_ratio == other.rupt_aspect_ratio
            and self.mfd == other.mfd and self.rake == other.rake
        )


class SimpleFaultGeometry(object):
    """Basic object representation of a geometry for a
    :class:`SimpleFaultSource`.

   :param str wkt:
        WKT representing the fault trace of a simple fault (a LINESTRING).
    :param float upper_seismo_depth:
        Upper seismogenic depth.
    :param float lower_seismo_depth:
        Lower siesmogenic depth.
    """

    def __init__(self, id=None, name=None, wkt=None, dip=None,
                 upper_seismo_depth=None, lower_seismo_depth=None):
        self.wkt = wkt
        self.dip = dip
        self.upper_seismo_depth = upper_seismo_depth
        self.lower_seismo_depth = lower_seismo_depth

    def __eq__(self, other):
        return (
            self.wkt == other.wkt and self.dip == other.dip
            and self.upper_seismo_depth == other.upper_seismo_depth
            and self.lower_seismo_depth == other.lower_seismo_depth
        )


class ComplexFaultSource(SimpleFaultSource):
    """Basic object representation of a Complex Fault Source.

    :param geometry:
        :class:`ComplexFaultGeometry` object.
    :param str mag_scale_rel:
        Magnitude Scaling Relationship.
    :param float rupt_aspect_ratio:
        Rupture Aspect Ratio.
    :param mfd:
        Magnitude Frequency Distribution. An instance of
        :class:`IncrementalMFD` or :class:`TGRMFD`.
    :param float rake:
        Rake angle.
    """


class ComplexFaultGeometry(object):
    """Basic object representation of a geometry for a
    :class:`ComplexFaultSource`.

    :param str top_edge_wkt:
        WKT representing the fault top edge (a LINESTRING).
    :param str bottom_edge_wkt:
        WKT representing the fault bottom edge (a LINESTRING).
    :param list int_edges:
        Intermediate fault edges, between the top edge and bottom edge.
        A `list` of `str` objects representing the WKT for each intermediate
        fault edge (each is a LINESTRING).

        This parameter is optional.
    """

    def __init__(self, top_edge_wkt=None, bottom_edge_wkt=None,
                 int_edges=None):
        self.top_edge_wkt = top_edge_wkt
        self.bottom_edge_wkt = bottom_edge_wkt
        self.int_edges = int_edges if int_edges is not None else []

    def __eq__(self, other):
        return (
            self.top_edge_wkt == other.top_edge_wkt
            and self.bottom_edge_wkt == other.bottom_edge_wkt
            and self.int_edges == other.int_edges
        )


class IncrementalMFD(object):
    """Basic object representation of an Incremental Magnitude Frequency
    Distribtion.

    :param float min_mag:
        The lowest possible magnitude for this MFD.
    :param float bin_width:
        Width of a single histogram bin.
    :param list occur_rates:
        `list` of occurrence rates (`float` values).
    """

    def __init__(self, min_mag=None, bin_width=None, occur_rates=None):
        self.min_mag = min_mag
        self.bin_width = bin_width
        self.occur_rates = occur_rates

    def __eq__(self, other):
        return (
            self.min_mag == other.min_mag and self.max_mag == other.max_mag
            and self.occur_rates == other.occur_rates
        )


class TGRMFD(object):
    """Basic object representation of a Truncated Gutenberg-Richter Magnitude
    Frequency Distribution.

    :param float a_val:
        10 ** a_val is the number of of earthquakes per year with magnitude
        greater than or equal to 0.
    :param float b_val:
        Decay rate of the exponential distribution.
    :param float min_mag:
        The lowest possible magnitude for this MFD.
    :param float max_mag:
        The highest possible magnitude for this MFD.
    """

    def __init__(self, a_val=None, b_val=None, min_mag=None, max_mag=None):
        self.a_val = a_val
        self.b_val = b_val
        self.min_mag = min_mag
        self.max_mag = max_mag

    def __eq__(self, other):
        return (
            self.a_val == other.a_val and self.b_val == other.b_val
            and self.min_mag == other.min_mag and self.max_mag == other.max_mag
        )


class NodalPlane(object):
    """Basic object representation of a single node in a Nodal Plane
    Distribution.

    :param float probability:
        Probability for this node in a Nodal Plane Distribution.
    :param float strike:
        Strike angle.
    :param float dip:
        Dip angle.
    :param float rake:
        Rake angle.
    """

    def __init__(self, probability=None, strike=None, dip=None, rake=None):
        self.probability = probability
        self.strike = strike
        self.dip = dip
        self.rake = rake

    def __eq__(self, other):
        return (
            self.probability == other.probability
            and self.strike == other.strike and self.dip == other.dip
            and self.rake == other.rake
        )
