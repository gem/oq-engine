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
COMMENT ON SCHEMA uiapi IS 'Data required by the API presented to the various OpenQuake UIs';

COMMENT ON TABLE admin.organization IS 'An organization that is utilising the OpenQuake database';
COMMENT ON TABLE admin.oq_user IS 'An OpenQuake user that is utilising the OpenQuake database';
COMMENT ON COLUMN admin.oq_user.data_is_open IS 'Whether the data owned by the user is visible to the general public.';
COMMENT ON TABLE admin.revision_info IS 'Facilitates the keeping of revision information for the OpenQuake database and/or its artefacts (schemas, tables etc.)';
COMMENT ON COLUMN admin.revision_info.artefact IS 'The name of the database artefact for which we wish to store revision information.';
COMMENT ON COLUMN admin.revision_info.revision IS 'The revision information for the associated database artefact.';
COMMENT ON COLUMN admin.revision_info.step IS 'A simple counter that will be used to facilitate schema upgrades and/or data migration.';
COMMENT ON COLUMN admin.revision_info.last_update IS 'The date/time when the revision information was last updated. Please note: this time stamp is not refreshed automatically. It is expected that schema/data migration scripts will modify this as appropriate.';

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
COMMENT ON COLUMN pshai.complex_fault.mfd_tgr_id IS 'Foreign key to a magnitude frequency distribution (truncated Gutenberg-Richter).';
COMMENT ON COLUMN pshai.complex_fault.mfd_evd_id IS 'Foreign key to a magnitude frequency distribution (evenly discretized).';
COMMENT ON COLUMN pshai.complex_fault.fault_edge_id IS 'Foreign key to a fault edge.';
COMMENT ON COLUMN pshai.complex_fault.outline IS 'The outline of the fault surface, computed by using the top/bottom fault edges.';

COMMENT ON VIEW pshai.complex_rupture IS 'A complex rupture view, needed for opengeo server integration.';
COMMENT ON VIEW pshai.complex_source IS 'A complex source view, needed for opengeo server integration.';

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
COMMENT ON COLUMN pshai.mfd_evd.min_val IS 'Minimum magnitude value.';
COMMENT ON COLUMN pshai.mfd_evd.max_val IS 'Maximum magnitude value (will be derived/calculated for evenly discretized magnitude frequency distributions).';

COMMENT ON TABLE pshai.mfd_tgr IS 'Magnitude frequency distribution, truncated Gutenberg-Richter.';
COMMENT ON COLUMN pshai.mfd_tgr.magnitude_type IS 'Magnitude type i.e. one of:
    - body wave magnitude (Mb)
    - duration magnitude (Md)
    - local magnitude (Ml)
    - surface wave magnitude (Ms)
    - moment magnitude (Mw)';
COMMENT ON COLUMN pshai.mfd_tgr.min_val IS 'Minimum magnitude value.';
COMMENT ON COLUMN pshai.mfd_tgr.max_val IS 'Maximum magnitude value.';

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

COMMENT ON VIEW pshai.simple_rupture IS 'A simple rupture view, needed for opengeo server integration.';
COMMENT ON VIEW pshai.simple_source IS 'A simple source view, needed for opengeo server integration.';
COMMENT ON TABLE pshai.source IS 'A seismic source, can be based on a point, area or a complex or simple fault.';
COMMENT ON COLUMN pshai.source.si_type IS 'The source''s seismic input type: can be one of: area, point, complex or simple.';
COMMENT ON COLUMN pshai.source.tectonic_region IS 'Tectonic region type i.e. one of:
    - Active Shallow Crust (active)
    - Stable Shallow Crust (stable)
    - Subduction Interface (interface)
    - Subduction IntraSlab (intraslab)
    - Volcanic             (volcanic)';

COMMENT ON TABLE uiapi.input IS 'A single OpenQuake input file uploaded by the user';
COMMENT ON COLUMN uiapi.input.input_type IS 'Input file type, one of:
    - source model file (source)
    - source logic tree (lt-source)
    - GMPE logic tree (lt-gmpe)
    - exposure file (exposure)
    - vulnerability file (vulnerability)';
COMMENT ON COLUMN uiapi.input.path IS 'The full path of the input file on the server';
COMMENT ON COLUMN uiapi.input.size IS 'Number of bytes in file';
COMMENT ON TABLE uiapi.oq_job IS 'Date related to an OpenQuake job that was created in the UI.';
COMMENT ON COLUMN uiapi.oq_job.description IS 'A description of the OpenQuake job, allows users to browse jobs and their inputs/outputs at a later point.';
COMMENT ON COLUMN uiapi.oq_job.job_type IS 'One of: classical, probabilistic or deterministic.';
COMMENT ON COLUMN uiapi.oq_job.status IS 'One of: created, in progress, failed or succeeded.';
COMMENT ON COLUMN uiapi.oq_job.duration IS 'The job''s duration in seconds (only available once the jobs terminates).';

COMMENT ON TABLE uiapi.oq_params IS 'Holds the parameters needed to invoke the OpenQuake engine.';
COMMENT ON COLUMN uiapi.oq_params.histories IS 'Number of seismicity histories';
COMMENT ON COLUMN uiapi.oq_params.imls IS 'Intensity measure levels';
COMMENT ON COLUMN uiapi.oq_params.imt IS 'Intensity measure type, one of:
    - peak ground acceleration (pga)
    - spectral acceleration (sa)
    - peak ground velocity (pgv)
    - peak ground displacement (pgd)';
COMMENT ON COLUMN uiapi.oq_params.poes IS 'Probabilities of exceedence';

COMMENT ON TABLE uiapi.upload IS 'A batch of OpenQuake input files uploaded by the user';
COMMENT ON COLUMN uiapi.upload.path IS 'The directory where the input files belonging to a batch live on the server';
