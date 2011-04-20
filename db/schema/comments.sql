/*
  Documentation for the OpenQuake database schema.
  Please keep these alphabetical by table.

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

COMMENT ON TABLE admin.organization IS 'An organization that is utilising the OpenQuake database';
COMMENT ON TABLE admin.oq_user IS 'An OpenQuake user that is utilising the OpenQuake database';
COMMENT ON COLUMN admin.oq_user.data_is_open IS 'Whether the data owned by the user is visible to the general public.';

COMMENT ON TABLE pshai.complex_fault IS 'A complex (fault) geometry, in essence a sequence of fault edges.';
COMMENT ON COLUMN pshai.complex_fault.gid IS 'An alpha-numeric identifier for this complex fault geometry.';
COMMENT ON COLUMN pshai.complex_fault.mfd_evd_id IS 'Foreign key to a magnitude frequency distribution (truncated Gutenberg-Richter).';
COMMENT ON COLUMN pshai.complex_fault.mfd_evd_id IS 'Foreign key to a magnitude frequency distribution (evenly discretized).';
COMMENT ON COLUMN pshai.complex_fault.mfd_evd_id IS 'Foreign key to a fault edge.';
COMMENT ON COLUMN pshai.complex_fault.outline IS 'The outline of the fault surface, computed by using the top/bottom fault edges.';

COMMENT ON TABLE pshai.fault_edge IS 'Part of a complex (fault) geometry, describes the top and the bottom seismic edges.';
COMMENT ON COLUMN pshai.fault_edge.bottom IS 'Bottom fault edge.';
COMMENT ON COLUMN pshai.fault_edge.top IS 'Top fault edge.';

COMMENT ON TABLE pshai.focal_mechanism IS 'Holds strike, dip and rake values with the respective constraints.';

COMMENT ON TABLE pshai.magnitude_type IS 'Enumeration of magnitude types.';

COMMENT ON TABLE pshai.mfd_evd IS 'Magnitude frequency distribution, evenly discretized.';

COMMENT ON TABLE pshai.mfd_tgr IS 'Magnitude frequency distribution, truncated Gutenberg-Richter.';

COMMENT ON TABLE pshai.r_depth_distr IS 'Rupture depth distribution.';

COMMENT ON TABLE pshai.r_rate_mdl IS 'Rupture rate model.';

COMMENT ON TABLE pshai.rupture IS 'A rupture, can be based on a point or a complex or simple fault.';
COMMENT ON COLUMN pshai.rupture.si_type IS 'The rupture''s seismic input type: can be one of: point, complex or simple.';

COMMENT ON TABLE pshai.simple_fault IS 'A simple fault geometry.';
COMMENT ON COLUMN pshai.simple_fault.dip IS 'The fault''s inclination angle with respect to the plane.';
COMMENT ON COLUMN pshai.simple_fault.upper_depth IS 'The upper seismogenic depth.';
COMMENT ON COLUMN pshai.simple_fault.lower_depth IS 'The lower seismogenic depth.';
COMMENT ON COLUMN pshai.simple_fault.outline IS 'The outline of the fault surface, computed by using the dip and the upper/lower seismogenic depth.';

COMMENT ON TABLE pshai.source IS 'A seismic source, can be based on a point, area or a complex or simple fault.';
COMMENT ON COLUMN pshai.source.si_type IS 'The source''s seismic input type: can be one of: area, point, complex or simple.';

COMMENT ON TABLE pshai.tectonic_region IS 'Enumeration of tectonic region types';
