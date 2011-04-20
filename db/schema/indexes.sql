/*
  Indexes for the OpenQuake database.

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License version 3
    only, as published by the Free Software Foundation.

    OpenQuake is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License version 3 for more details
   a copy is included in the LICENSE file that accompanied this code).

    You should have received a copy of the GNU Lesser General Public License
    version 3 along with OpenQuake.  If not, see
    <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.
*/


-- fault_edge
CREATE INDEX pshai_fault_edge_bottom_idx ON pshai.fault_edge USING gist(bottom);
CREATE INDEX pshai_fault_edge_top_idx ON pshai.fault_edge USING gist(top);

-- rupture
CREATE INDEX pshai_rupture_point_idx ON pshai.rupture USING gist(point);

-- simple_fault
CREATE INDEX pshai_simple_fault_geom_idx ON pshai.simple_fault USING gist(geom);

-- source
CREATE INDEX pshai_source_area_idx ON pshai.source USING gist(area);
CREATE INDEX pshai_source_point_idx ON pshai.source USING gist(point);
