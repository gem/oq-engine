# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2026 GEM Foundation
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
Example script that can be read within RunTimeSourceModelLT to construct
an SSC logic tree at runtime instead of reading in from XMLs.

Builds a simple 20 branch logic tree (2 b-values x 10 activity rates) from
CSV data files by returning a list of (name, weight, xml_str) triples.

Each branch contains one area source and one simple fault source.
"""
import os
import numpy as np
import csv

DATA_DIR = os.path.join(os.path.dirname(__file__), 'ssc_runtime_input_data')


def _load_csv(fname):
    with open(os.path.join(DATA_DIR, fname)) as f:
        return list(csv.DictReader(f))


def _get_coords(rows):
    return ' '.join(f'{r["lon"]} {r["lat"]}' for r in rows)


def _a_value(rate, b_value, ref_mag):
    return np.log10(rate) + b_value * float(ref_mag)


def _build_xml(branch_idx, area_rows, fault_rows, b, ref_mag, rate):
    area_coords = _get_coords(area_rows)
    fault_coords = _get_coords(fault_rows)
    a_area = _a_value(0.9 * rate, b, ref_mag)
    a_fault = _a_value(0.1 * rate, b, ref_mag)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"\n'
        '      xmlns:gml="http://www.opengis.net/gml">\n'
        f'    <sourceModel name="branch_{branch_idx:03d}">\n'
        f'        <sourceGroup name="grp_1"'
        f' tectonicRegion="Active Shallow Crust">\n'
        f'            <areaSource id="as1" name="area_src"'
        f' tectonicRegion="Active Shallow Crust">\n'
        f'                <areaGeometry>\n'
        f'                    <gml:Polygon>\n'
        f'                        <gml:exterior>\n'
        f'                            <gml:LinearRing>\n'
        f'                                <gml:posList>'
        f'{area_coords}</gml:posList>\n'
        f'                            </gml:LinearRing>\n'
        f'                        </gml:exterior>\n'
        f'                    </gml:Polygon>\n'
        f'                    <upperSeismoDepth>0.0</upperSeismoDepth>\n'
        f'                    <lowerSeismoDepth>20.0</lowerSeismoDepth>\n'
        f'                </areaGeometry>\n'
        f'                <magScaleRel>WC1994</magScaleRel>\n'
        f'                <ruptAspectRatio>1.5</ruptAspectRatio>\n'
        f'                <truncGutenbergRichterMFD'
        f' aValue="{a_area:.4f}" bValue="{b:.2f}"'
        f' minMag="5.0" maxMag="7.5"/>\n'
        f'                <nodalPlaneDist>\n'
        f'                    <nodalPlane probability="1.0"'
        f' strike="0.0" dip="90.0" rake="0.0"/>\n'
        f'                </nodalPlaneDist>\n'
        f'                <hypoDepthDist>\n'
        f'                    <hypoDepth probability="1.0"'
        f' depth="10.0"/>\n'
        f'                </hypoDepthDist>\n'
        f'            </areaSource>\n'
        f'            <simpleFaultSource id="fs1" name="fault_src"'
        f' tectonicRegion="Active Shallow Crust">\n'
        f'                <simpleFaultGeometry>\n'
        f'                    <gml:LineString>\n'
        f'                        <gml:posList>'
        f'{fault_coords}</gml:posList>\n'
        f'                    </gml:LineString>\n'
        f'                    <dip>60.0</dip>\n'
        f'                    <upperSeismoDepth>0.0</upperSeismoDepth>\n'
        f'                    <lowerSeismoDepth>15.0</lowerSeismoDepth>\n'
        f'                </simpleFaultGeometry>\n'
        f'                <magScaleRel>WC1994</magScaleRel>\n'
        f'                <ruptAspectRatio>1.5</ruptAspectRatio>\n'
        f'                <truncGutenbergRichterMFD'
        f' aValue="{a_fault:.4f}" bValue="{b:.2f}"'
        f' minMag="5.0" maxMag="7.5"/>\n'
        f'                <rake>0.0</rake>\n'
        f'            </simpleFaultSource>\n'
        f'        </sourceGroup>\n'
        f'    </sourceModel>\n'
        f'</nrml>\n'
    )


def get_source_model_lt():
    """
    Entry-point for RuntimeSourceModelLT which in effect creates
    the realisations on a source-by-source basis, each represented
    by an XML string.

    Returns list of (name, weight, xml_str) triples. The regular
    checks on the logic tree such as the weights of the branches
    summing to 1.0 is still checked as for regular XML-based SSC
    LTs inside the engine.

    NOTE: A function with exactly this name is checked for within
    RuntimeSourceModelLT and it is expected to retun the list of
    (name, weight, xml_str) triples. If this function is missing
    or does not return the expected triples the engine will raise
    an error.

    NOTE: The runtime approach demonstrated in this QA test only
    currently supports the specification of each branch as a seperate
    XML (i.e., the use of branching levels which consider features
    such as applyToSources to apply epistemic uncertainties is not
    possible). However, the point of this feature is to support the
    generation of complex logic trees at runtime, so it is expected
    that the user is comfortable with fully describing their logic tree
    on a branch-by-branch basis using a python script if they are
    exploring this capability.
    """
    # Load the data
    area_rows = _load_csv('area_polygon.csv')
    fault_rows = _load_csv('fault_trace.csv')
    recurset = _load_csv('recurset.csv')

    # Build the sources
    branches = []
    for i, row in enumerate(recurset):
        b = float(row['b_value'])
        ref_mag = float(row['ref_mag'])
        rate = float(row['rate'])
        weight = float(row['weight'])
        xml_str = _build_xml(i, area_rows, fault_rows, b, ref_mag, rate)
        branches.append((f'branch_{i:03d}', weight, xml_str))

    return branches # Fed into RuntimeSourceModelLT
