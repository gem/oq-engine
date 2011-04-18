/*
  Add Comments to the OpenQuake database. Please keep these alphabetical by
  table.

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License version 3
    only, as published by the Free Software Foundation.

    OpenQuake is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License version 3 for more details
    (a copy is included in the LICENSE file that accompanied this code).

    You should have received a copy of the GNU Lesser General Public License
    version 3 along with OpenQuake.  If not, see
    <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.
*/

COMMENT ON TABLE pshai.complex_fault IS 'A complex (fault) geometry, in essence a sequence of fault edges.';
COMMENT ON COLUMN pshai.complex_fault.gid IS 'An alpha-numeric identifier for this complex fault geometry.';

COMMENT ON TABLE pshai.fault_edge IS 'Part of a complex (fault) geometry, describes the top and the bottom seismic edges.';

COMMENT ON TABLE pshai.magnitude_type IS 'Enumeration of magnitude types.';

COMMENT ON TABLE pshai.mfd_evd IS 'Magnitude frequency distribution, evenly discretized.';

COMMENT ON TABLE pshai.mfd_tgr IS 'Magnitude frequency distribution, truncated Gutenberg-Richter.';

COMMENT ON TABLE pshai.r_depth_distr IS 'Rupture depth distribution.';

COMMENT ON TABLE pshai.r_rate_mdl IS 'Rupture rate model.';

COMMENT ON TABLE pshai.rupture IS 'A rupture, can be complex or simple.';

COMMENT ON TABLE pshai.simple_fault IS 'A simple fault geometry.';

COMMENT ON TABLE pshai.source IS 'A fault source, can be complex or simple.';

COMMENT ON TABLE pshai.focal_mechanism IS 'Holds strike, dip and rake values with the respective constraints.';

COMMENT ON TABLE pshai.tectonic_region IS 'Enumeration of tectonic region types';

