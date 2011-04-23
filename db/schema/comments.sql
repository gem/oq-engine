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

COMMENT ON DATABASE my_database IS 'OpenQuake database (http://openquake.org/)';

COMMENT ON SCHEMA admin IS 'Administrative data';
COMMENT ON SCHEMA eqcat IS 'Earthquake catalog';
COMMENT ON SCHEMA pshai IS 'PSHA input model';

COMMENT ON TABLE admin.organization IS 'An organization that is utilising the OpenQuake database';
COMMENT ON TABLE admin.oq_user IS 'An OpenQuake user that is utilising the OpenQuake database';
COMMENT ON COLUMN admin.oq_user.data_is_open IS 'Whether the data owned by the user is visible to the general public.';
COMMENT ON TABLE admin.revision_info IS 'Facilitates the keeping of revision information for the OpenQuake database and/or its artefacts (schemas, tables etc.)';
COMMENT ON COLUMN admin.revision_info.artefact IS 'The name of the database artefact for which we wish to store revision information.';
COMMENT ON COLUMN admin.revision_info.revision IS 'The revision information for the associated database artefact.';

COMMENT ON TABLE eqcat.catalog IS 'Table with earthquake catalog data, the magnitude(s) and the event surface is kept in separate tables.';
COMMENT ON COLUMN eqcat.catalog.depth IS 'Earthquake depth (in km)';
COMMENT ON COLUMN eqcat.catalog.event_class IS 'Either unknown (NULL) or one of: ''aftershock'', ''foreshock''.';
COMMENT ON COLUMN eqcat.catalog.magnitude_id IS 'Foreign key to the row with the magnitude data.';
COMMENT ON COLUMN eqcat.catalog.surface_id IS 'Foreign key to the row with the earthquake surface data.';
COMMENT ON COLUMN eqcat.catalog.time IS 'Earthquake date and time';

COMMENT ON TABLE eqcat.magnitude IS 'Table with earthquake magnitudes in different units of measurement. At least one magnitude value must be set.';

COMMENT ON TABLE eqcat.surface IS 'Table with earthquake surface data, basically an ellipse and a strike angle.';
COMMENT ON COLUMN eqcat.surface.semi_minor IS 'Semi-minor axis: The shortest radius of an ellipse.';
COMMENT ON COLUMN eqcat.surface.semi_major IS 'Semi-major axis: The longest radius of an ellipse.';

COMMENT ON TABLE pshai.complex_fault IS 'A complex (fault) geometry, in essence a sequence of fault edges. However, we only support a single fault edge at present.';
COMMENT ON COLUMN pshai.complex_fault.gid IS 'An alpha-numeric identifier for this complex fault geometry.';
COMMENT ON COLUMN pshai.complex_fault.mfd_evd_id IS 'Foreign key to a magnitude frequency distribution (truncated Gutenberg-Richter).';
COMMENT ON COLUMN pshai.complex_fault.mfd_evd_id IS 'Foreign key to a magnitude frequency distribution (evenly discretized).';
COMMENT ON COLUMN pshai.complex_fault.mfd_evd_id IS 'Foreign key to a fault edge.';
COMMENT ON COLUMN pshai.complex_fault.outline IS 'The outline of the fault surface, computed by using the top/bottom fault edges.';

COMMENT ON TABLE pshai.fault_edge IS 'Part of a complex (fault) geometry, describes the top and the bottom seismic edges.';
COMMENT ON COLUMN pshai.fault_edge.bottom IS 'Bottom fault edge.';
COMMENT ON COLUMN pshai.fault_edge.top IS 'Top fault edge.';

COMMENT ON TABLE pshai.focal_mechanism IS 'Holds strike, dip and rake values with the respective constraints.';

COMMENT ON TABLE pshai.mfd_evd IS 'Magnitude frequency distribution, evenly discretized.';
COMMENT ON COLUMN pshai.mfd_evd.magnitude_type IS 'Magnitude type i.e. one of:
    - body wave magnitude (Mb)
    - duration magnitude (Md)
    - local magnitude (Ml)
    - surface wave magnitude (Ms)
    - moment magnitude (Mw)';

COMMENT ON TABLE pshai.mfd_tgr IS 'Magnitude frequency distribution, truncated Gutenberg-Richter.';
COMMENT ON COLUMN pshai.mfd_tgr.magnitude_type IS 'Magnitude type i.e. one of:
    - body wave magnitude (Mb)
    - duration magnitude (Md)
    - local magnitude (Ml)
    - surface wave magnitude (Ms)
    - moment magnitude (Mw)';

COMMENT ON TABLE pshai.r_depth_distr IS 'Rupture depth distribution.';
COMMENT ON COLUMN pshai.r_depth_distr.magnitude_type IS 'Magnitude type i.e. one of:
    - body wave magnitude (Mb)
    - duration magnitude (Md)
    - local magnitude (Ml)
    - surface wave magnitude (Ms)
    - moment magnitude (Mw)';

COMMENT ON TABLE pshai.r_rate_mdl IS 'Rupture rate model.';

COMMENT ON TABLE pshai.rupture IS 'A rupture, can be based on a point or a complex or simple fault.';
COMMENT ON COLUMN pshai.rupture.si_type IS 'The rupture''s seismic input type: can be one of: point, complex or simple.';
COMMENT ON COLUMN pshai.rupture.magnitude_type IS 'Magnitude type i.e. one of:
    - body wave magnitude (Mb)
    - duration magnitude (Md)
    - local magnitude (Ml)
    - surface wave magnitude (Ms)
    - moment magnitude (Mw)';
COMMENT ON COLUMN pshai.rupture.tectonic_region IS 'Tectonic region type i.e. one of:
    - Active Shallow Crust (active)
    - Stable Shallow Crust (stable)
    - Subduction Interface (interface)
    - Subduction IntraSlab (intraslab)
    - Volcanic             (volcanic)';

COMMENT ON TABLE pshai.simple_fault IS 'A simple fault geometry.';
COMMENT ON COLUMN pshai.simple_fault.dip IS 'The fault''s inclination angle with respect to the plane.';
COMMENT ON COLUMN pshai.simple_fault.upper_depth IS 'The upper seismogenic depth.';
COMMENT ON COLUMN pshai.simple_fault.lower_depth IS 'The lower seismogenic depth.';
COMMENT ON COLUMN pshai.simple_fault.outline IS 'The outline of the fault surface, computed by using the dip and the upper/lower seismogenic depth.';

COMMENT ON TABLE pshai.source IS 'A seismic source, can be based on a point, area or a complex or simple fault.';
COMMENT ON COLUMN pshai.source.si_type IS 'The source''s seismic input type: can be one of: area, point, complex or simple.';
COMMENT ON COLUMN pshai.source.tectonic_region IS 'Tectonic region type i.e. one of:
    - Active Shallow Crust (active)
    - Stable Shallow Crust (stable)
    - Subduction Interface (interface)
    - Subduction IntraSlab (intraslab)
    - Volcanic             (volcanic)';
