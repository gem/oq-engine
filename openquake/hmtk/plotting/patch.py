# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2025 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from numpy import asarray, concatenate, ones


class Polygon(object):
    # Adapt Shapely or GeoJSON/geo_interface polygons to a common interface
    def __init__(self, context):
        if isinstance(context, dict):
            self.context = context["coordinates"]
        else:
            self.context = context

    @property
    def exterior(self):
        return getattr(self.context, "exterior", None) or self.context[0]

    @property
    def interiors(self):
        value = getattr(self.context, "interiors", None)
        if value is None:
            value = self.context[1:]
        return value


def PolygonPatch(polygon, **kwargs):
    """Constructs a matplotlib patch from a geometric object

    The `polygon` may be a Shapely or GeoJSON-like object possibly with holes.
    The `kwargs` are those supported by the matplotlib.patches.Polygon class
    constructor. Returns an instance of matplotlib.patches.PathPatch.

    Example (using Shapely Point and a matplotlib axes):

      >> b = Point(0, 0).buffer(1.0)
      >> patch = PolygonPatch(b, fc='blue', ec='blue', alpha=0.5)
      >> axis.add_patch(patch)
    """

    def coding(ob):
        # The codes will be all "LINETO" commands, except for "MOVETO"s at the
        # beginning of each subpath
        n = len(getattr(ob, "coords", None) or ob)
        vals = ones(n, dtype=Path.code_type) * Path.LINETO
        vals[0] = Path.MOVETO
        return vals

    if hasattr(polygon, "geom_type"):  # Shapely
        ptype = polygon.geom_type
        if ptype == "Polygon":
            polygon = [Polygon(polygon)]
        elif ptype == "MultiPolygon":
            polygon = [Polygon(p) for p in polygon]
        else:
            raise ValueError(
                "A polygon or multi-polygon representation is required"
            )

    else:  # GeoJSON
        polygon = getattr(polygon, "__geo_interface__", polygon)
        ptype = polygon["type"]
        if ptype == "Polygon":
            polygon = [Polygon(polygon)]
        elif ptype == "MultiPolygon":
            polygon = [Polygon(p) for p in polygon["coordinates"]]
        else:
            raise ValueError(
                "A polygon or multi-polygon representation is required"
            )

    vertices, codes = [], []
    for t in polygon:
        vertices.append(
            concatenate(
                [asarray(t.exterior.coords)[:, :2]]
                + [asarray(r.coords)[:, :2] for r in t.interiors]
            )
        )
        codes.append(
            concatenate(
                [coding(t.exterior)] + [coding(r) for r in t.interiors]
            )
        )
    return PathPatch(Path(concatenate(vertices), concatenate(codes)), **kwargs)


def debug_plot(*polygons):
    import matplotlib.pyplot as plt

    _fig, ax = plt.subplots()
    for polygon in polygons:
        pol = polygon._polygon2d
        x1, y1, x2, y2 = pol.bounds
        ax.set_xlim([x1, x2])
        ax.set_ylim([y1, y2])
        ax.add_patch(PolygonPatch(pol, alpha=0.2))
    plt.show()
