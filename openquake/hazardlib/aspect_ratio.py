# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026, GEM Foundation
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

from openquake.baselib.node import Node


class MagDepAspectRatio:
    """
    Class to handle magnitude-dependent aspect ratios described by
    piecewise expressions which are evaluated during rup generation.
    """
    def __init__(self, func_type, mag_points):
        self.func_type = func_type    # Type of expression to evaluate
        self.mag_points = mag_points  # List of (mag, aratio), ascending mag

    @classmethod
    def from_dict(cls, d):
        return cls(d["type"], d["function"])

    def get(self, mag):
        if self.func_type == "linear_piecewise":
            mags = [m for m, _ in self.mag_points]
            aratios = [a for _, a in self.mag_points]
            if mag <= mags[0]:
                return aratios[0]
            if mag >= mags[-1]:
                return aratios[-1]
            for i in range(len(mags) - 1):
                if mags[i] <= mag <= mags[i + 1]:
                    t = (mag - mags[i]) / (mags[i + 1] - mags[i])
                    return aratios[i] + t * (aratios[i + 1] - aratios[i])
        raise ValueError(
            f"Unsupported aspectRatioFunction type: {self.func_type}")


### Aspect Ratio Utils ###
def get_aspect_ratio(node):
    """
    Parse an aspect ratio XML node, returning either a float or a
    MagDepAspectRatio for the magnitude-dependent form.
    """
    try:
        # check if mag-dependent aratio
        arf = node.aspectRatioFunction
    except AttributeError:
        # Regular
        return ~node.ruptAspectRatio

    # Get the function type
    func_type = ~arf.type
    
    if func_type == 'linear_piecewise':
        npoints = len(arf.mag_points)
        if npoints != 2:
            raise ValueError(
                f"Should be two elements [(MinAR, MinMmin), (MaxAR, Mmax)] "
                f"in linear_piecewise kind of ruptAspectRatio ({npoints})")
        points = [(float(p['mag']), float(p['aratio'])) for p in arf.mag_points]
        if any(m <= 0 for m, _ in points):
            raise ValueError(
                f"aspectRatioFunction magnitudes must be positive: "
                f"{[m for m, _ in points]}")
        if points[0][0] >= points[1][0]:
            raise ValueError(
                f"aspectRatioFunction points must be in ascending magnitude "
                f"order: mag[0]={points[0][0]} >= mag[1]={points[1][0]}")
        return MagDepAspectRatio("linear_piecewise", points)

    raise ValueError(f"Unsupported aspectRatioFunction type: {func_type}")


def build_aspect_ratio_node(rar): # Used in sourcewriter and geopackager
    """
    Build an aspect ratio node from either a regular float or a
    MagDepAspectRatio class instance.
    """
    if not isinstance(rar, MagDepAspectRatio):
        # Regular aspect ratio as float
        return Node("ruptAspectRatio", text=rar)
    
    # Must be MagDepAspectRatio
    if rar.func_type == "linear_piecewise":
        point_nodes = [Node("mag_point", {"mag": m, "aratio": a})
                       for m, a in rar.mag_points]
        return Node("aspectRatioFunction", nodes=[
            Node("type", text="linear_piecewise"),
            Node("mag_points", nodes=point_nodes)])
    
    raise ValueError(f"Unsupported aspectRatioFunction type: {rar.func_type}")
