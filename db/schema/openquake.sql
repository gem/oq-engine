/*
  OpenQuake database schema definitions.

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


------------------------------------------------------------------------
-- Name space definitions go here
------------------------------------------------------------------------
CREATE SCHEMA admin;
CREATE SCHEMA eqcat;
CREATE SCHEMA pshai;
CREATE SCHEMA uiapi;


------------------------------------------------------------------------
-- Table definitions go here
------------------------------------------------------------------------


-- Organization
CREATE TABLE admin.organization (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    address VARCHAR,
    url VARCHAR,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE admin_ts;


-- OpenQuake users
CREATE TABLE admin.oq_user (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR NOT NULL,
    full_name VARCHAR NOT NULL,
    organization_id INTEGER NOT NULL,
    -- Whether the data owned by the user is visible to the general public.
    data_is_open boolean NOT NULL DEFAULT TRUE,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE admin_ts;


-- Revision information
CREATE TABLE admin.revision_info (
    id SERIAL PRIMARY KEY,
    artefact VARCHAR NOT NULL,
    revision VARCHAR NOT NULL,
    -- The step will be used for schema upgrades and data migrations.
    step INTEGER NOT NULL DEFAULT 0,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE admin_ts;


-- Earthquake catalog
CREATE TABLE eqcat.catalog (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- This is *not* a foreign key.
    eventid INTEGER NOT NULL,
    agency VARCHAR NOT NULL,
    identifier VARCHAR NOT NULL,
    time timestamp without time zone NOT NULL,
    -- error in seconds
    time_error float NOT NULL,
    -- depth in km
    depth float NOT NULL,
    -- error in km
    depth_error float NOT NULL,
    -- One of unknown, aftershock or foreshock
    event_class VARCHAR,
        CONSTRAINT event_class_value CHECK (
            event_class is NULL
            OR (event_class IN ('aftershock', 'foreshock'))),
    magnitude_id INTEGER NOT NULL,
    surface_id INTEGER NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE eqcat_ts;
SELECT AddGeometryColumn('eqcat', 'catalog', 'point', 4326, 'POINT', 2);
ALTER TABLE eqcat.catalog ALTER COLUMN point SET NOT NULL;


-- Earthquake event magnitudes
CREATE TABLE eqcat.magnitude (
    id SERIAL PRIMARY KEY,
    mb_val float,
    mb_val_error float,
    ml_val float,
    ml_val_error float,
    ms_val float,
    ms_val_error float,
    mw_val float,
    mw_val_error float,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE eqcat_ts;


-- Earthquake event surface (an ellipse with an angle)
CREATE TABLE eqcat.surface (
    id SERIAL PRIMARY KEY,
    -- Semi-minor axis: The shortest radius of an ellipse.
    semi_minor float NOT NULL,
    -- Semi-major axis: The longest radius of an ellipse.
    semi_major float NOT NULL,
    strike float NOT NULL,
        CONSTRAINT strike_value CHECK ((strike >= 0.0) AND (strike <= 360.0)),
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE eqcat_ts;

-- global catalog view, needed for Geonode integration
CREATE VIEW eqcat.catalog_allfields AS
SELECT
    eqcat.catalog.*,
    eqcat.surface.semi_minor, eqcat.surface.semi_major,
    eqcat.surface.strike,
    eqcat.magnitude.mb_val, eqcat.magnitude.mb_val_error,
    eqcat.magnitude.ml_val, eqcat.magnitude.ml_val_error,
    eqcat.magnitude.ms_val, eqcat.magnitude.ms_val_error,
    eqcat.magnitude.mw_val, eqcat.magnitude.mw_val_error
FROM eqcat.catalog, eqcat.magnitude, eqcat.surface
WHERE
    eqcat.catalog.magnitude_id = eqcat.magnitude.id
    AND eqcat.catalog.surface_id = eqcat.surface.id;

-- rupture
CREATE TABLE pshai.rupture (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- Associates the rupture with a source model input file (uploaded by a GUI
    -- user).
    input_id INTEGER,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    -- seismic input type
    si_type VARCHAR NOT NULL DEFAULT 'simple'
        CONSTRAINT si_type CHECK (si_type IN ('complex', 'point', 'simple')),
    -- Tectonic region type, one of:
    --      Active Shallow Crust (active)
    --      Stable Shallow Crust (stable)
    --      Subduction Interface (interface)
    --      Subduction IntraSlab (intraslab)
    --      Volcanic             (volcanic)
    tectonic_region VARCHAR NOT NULL CONSTRAINT tect_region_val
        CHECK(tectonic_region IN (
            'active', 'stable', 'interface', 'intraslab', 'volcanic')),
    rake float,
        CONSTRAINT rake_value CHECK (
            rake is NULL OR ((rake >= -180.0) AND (rake <= 180.0))),
    magnitude float NOT NULL,
    -- One of:
    --      body wave magnitude (Mb)
    --      duration magnitude (Md)
    --      local magnitude (Ml)
    --      surface wave magnitude (Ms)
    --      moment magnitude (Mw)
    magnitude_type VARCHAR(2) NOT NULL DEFAULT 'Mw' CONSTRAINT mage_type_val
        CHECK(magnitude_type IN ('Mb', 'Md', 'Ml', 'Ms', 'Mw')),
    simple_fault_id INTEGER,
    complex_fault_id INTEGER,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;
SELECT AddGeometryColumn('pshai', 'rupture', 'point', 4326, 'POINT', 3);


-- source
CREATE TABLE pshai.source (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- Associates the source with a source model input file (uploaded by a GUI
    -- user).
    input_id INTEGER,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    -- seismic input type
    si_type VARCHAR NOT NULL DEFAULT 'simple'
        CONSTRAINT si_type CHECK
        (si_type IN ('area', 'point', 'complex', 'simple')),
    -- Tectonic region type, one of:
    --      Active Shallow Crust (active)
    --      Stable Shallow Crust (stable)
    --      Subduction Interface (interface)
    --      Subduction IntraSlab (intraslab)
    --      Volcanic             (volcanic)
    tectonic_region VARCHAR NOT NULL CONSTRAINT tect_region_val
        CHECK(tectonic_region IN (
            'active', 'stable', 'interface', 'intraslab', 'volcanic')),
    simple_fault_id INTEGER,
    complex_fault_id INTEGER,
    rake float,
        CONSTRAINT rake_value CHECK (
            rake is NULL OR ((rake >= -180.0) AND (rake <= 180.0))),
    -- hypocentral depth and the rupture depth distribution are only set for
    -- point/area sources
    hypocentral_depth float,
    r_depth_distr_id INTEGER,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;
SELECT AddGeometryColumn('pshai', 'source', 'point', 4326, 'POINT', 2);
SELECT AddGeometryColumn('pshai', 'source', 'area', 4326, 'POLYGON', 2);


-- Simple fault geometry
CREATE TABLE pshai.simple_fault (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    dip float NOT NULL
        CONSTRAINT dip_value CHECK ((dip >= 0.0) AND (dip <= 90.0)),
    upper_depth float NOT NULL
        CONSTRAINT upper_depth_val CHECK (upper_depth >= 0.0),
    lower_depth float NOT NULL
        CONSTRAINT lower_depth_val CHECK (lower_depth >= 0.0),
    mfd_tgr_id INTEGER,
    mfd_evd_id INTEGER,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;
SELECT AddGeometryColumn('pshai', 'simple_fault', 'edge', 4326, 'LINESTRING', 3);
ALTER TABLE pshai.simple_fault ALTER COLUMN edge SET NOT NULL;
SELECT AddGeometryColumn('pshai', 'simple_fault', 'outline', 4326, 'POLYGON', 3);


-- simple source view, needed for Opengeo server integration
CREATE VIEW pshai.simple_source (
    id, owner_id, input_id, gid, name, description, si_type, tectonic_region,
    rake, simple_fault, fault_outline) AS
SELECT
    src.id, src.owner_id, src.input_id, src.gid, src.name, src.description,
    src.si_type, src.tectonic_region, src.rake, sfault.edge, sfault.outline
FROM
    pshai.source src, pshai.simple_fault sfault
WHERE
    src.si_type = 'simple'
    AND src.simple_fault_id = sfault.id;


-- simple rupture view, needed for Opengeo server integration
CREATE VIEW pshai.simple_rupture (
    id, owner_id, input_id, gid, name, description, si_type, tectonic_region,
    rake, magnitude, magnitude_type, edge, fault_outline) AS
SELECT
    rup.id, rup.owner_id, rup.input_id, rup.gid, rup.name, rup.description,
    rup.si_type, rup.tectonic_region, rup.rake, rup.magnitude,
    rup.magnitude_type, sfault.edge, sfault.outline
FROM
    pshai.rupture rup, pshai.simple_fault sfault
WHERE
    rup.si_type = 'simple'
    AND rup.simple_fault_id = sfault.id;


-- Complex fault geometry
CREATE TABLE pshai.complex_fault (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    mfd_tgr_id INTEGER,
    mfd_evd_id INTEGER,
    fault_edge_id INTEGER NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;
SELECT AddGeometryColumn('pshai', 'complex_fault', 'outline', 4326, 'POLYGON', 3);


-- Fault edge
CREATE TABLE pshai.fault_edge (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;
SELECT AddGeometryColumn('pshai', 'fault_edge', 'top', 4326, 'LINESTRING', 3);
SELECT AddGeometryColumn('pshai', 'fault_edge', 'bottom', 4326, 'LINESTRING', 3);
ALTER TABLE pshai.fault_edge ALTER COLUMN top SET NOT NULL;
ALTER TABLE pshai.fault_edge ALTER COLUMN bottom SET NOT NULL;


-- complex source view, needed for Opengeo server integration
CREATE VIEW pshai.complex_source (
    id, owner_id, input_id, gid, name, description, si_type, tectonic_region,
    rake, top_edge, bottom_edge, fault_outline) AS
SELECT
    src.id, src.owner_id, src.input_id, src.gid, src.name, src.description,
    src.si_type, src.tectonic_region, src.rake, fedge.top, fedge.bottom,
    cfault.outline
FROM
    pshai.source src, pshai.complex_fault cfault, pshai.fault_edge fedge
WHERE
    src.si_type = 'complex'
    AND src.complex_fault_id = cfault.id AND cfault.fault_edge_id = fedge.id;


-- complex rupture view, needed for Opengeo server integration
CREATE VIEW pshai.complex_rupture (
    id, owner_id, input_id, gid, name, description, si_type, tectonic_region,
    rake, magnitude, magnitude_type, top_edge, bottom_edge, fault_outline) AS
SELECT
    rup.id, rup.owner_id, rup.input_id, rup.gid, rup.name, rup.description,
    rup.si_type, rup.tectonic_region, rup.rake, rup.magnitude,
    rup.magnitude_type, fedge.top, fedge.bottom, cfault.outline
FROM
    pshai.rupture rup, pshai.complex_fault cfault, pshai.fault_edge fedge
WHERE
    rup.si_type = 'complex'
    AND rup.complex_fault_id = cfault.id AND cfault.fault_edge_id = fedge.id;


-- Magnitude frequency distribution, Evenly discretized
CREATE TABLE pshai.mfd_evd (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- One of:
    --      body wave magnitude (Mb)
    --      duration magnitude (Md)
    --      local magnitude (Ml)
    --      surface wave magnitude (Ms)
    --      moment magnitude (Mw)
    magnitude_type VARCHAR(2) NOT NULL DEFAULT 'Mw' CONSTRAINT mage_type_val
        CHECK(magnitude_type IN ('Mb', 'Md', 'Ml', 'Ms', 'Mw')),
    min_val float NOT NULL,
    -- The maximum magnitude value will be derived/calculated for evenly
    -- discretized magnitude frequency distributions.
    -- It is initialized with a value that should never occur in practice.
    max_val float NOT NULL DEFAULT -1.0,
    bin_size float NOT NULL,
    mfd_values float[] NOT NULL,
    total_cumulative_rate float,
    total_moment_rate float,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;


-- Magnitude frequency distribution, Truncated Gutenberg Richter
CREATE TABLE pshai.mfd_tgr (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- One of:
    --      body wave magnitude (Mb)
    --      duration magnitude (Md)
    --      local magnitude (Ml)
    --      surface wave magnitude (Ms)
    --      moment magnitude (Mw)
    magnitude_type VARCHAR(2) NOT NULL DEFAULT 'Mw' CONSTRAINT mage_type_val
        CHECK(magnitude_type IN ('Mb', 'Md', 'Ml', 'Ms', 'Mw')),
    min_val float NOT NULL,
    max_val float NOT NULL,
    a_val float NOT NULL,
    b_val float NOT NULL,
    total_cumulative_rate float,
    total_moment_rate float,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;


-- Rupture depth distribution
CREATE TABLE pshai.r_depth_distr (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    -- One of:
    --      body wave magnitude (Mb)
    --      duration magnitude (Md)
    --      local magnitude (Ml)
    --      surface wave magnitude (Ms)
    --      moment magnitude (Mw)
    magnitude_type VARCHAR(2) NOT NULL DEFAULT 'Mw' CONSTRAINT mage_type_val
        CHECK(magnitude_type IN ('Mb', 'Md', 'Ml', 'Ms', 'Mw')),
    magnitude float[] NOT NULL,
    depth float[] NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;


-- Rupture rate model
CREATE TABLE pshai.r_rate_mdl (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    mfd_tgr_id INTEGER,
    mfd_evd_id INTEGER,
    focal_mechanism_id INTEGER NOT NULL,
    -- There can be 1+ rupture rate models associated with a seismic source
    -- that's why the foreign key sits here.
    source_id INTEGER NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;


CREATE TABLE pshai.focal_mechanism (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    strike float,
        CONSTRAINT strike_value CHECK (
            strike is NULL OR ((strike >= 0.0) AND (strike <= 360.0))),
    dip float,
        CONSTRAINT dip_value CHECK (
            dip is NULL OR ((dip >= 0.0) AND (dip <= 90.0))),
    rake float,
        CONSTRAINT rake_value CHECK (
            rake is NULL OR ((rake >= -180.0) AND (rake <= 180.0))),
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;


-- A batch of OpenQuake input files uploaded by the user
CREATE TABLE uiapi.upload (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- A user is looking for a batch of files uploaded in the past. How is he
    -- supposed to find or recognize them? Maybe a description might help..?
    description VARCHAR NOT NULL DEFAULT '',
    -- The directory where the input files belonging to a batch live on the
    -- server
    path VARCHAR NOT NULL UNIQUE,
    -- One of: pending, running, failed, succeeded
    status VARCHAR NOT NULL DEFAULT 'pending' CONSTRAINT upload_status_value
        CHECK(status IN ('pending', 'running', 'failed', 'succeeded')),
    job_pid INTEGER NOT NULL DEFAULT 0,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;


-- A single OpenQuake input file uploaded by the user
CREATE TABLE uiapi.input (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    upload_id INTEGER NOT NULL,
    -- The full path of the input file on the server
    path VARCHAR NOT NULL UNIQUE,
    -- Input file type, one of:
    --      source model file (source)
    --      source logic tree (lt_source)
    --      GMPE logic tree (lt_gmpe)
    --      exposure file (exposure)
    --      vulnerability file (vulnerability)
    input_type VARCHAR NOT NULL CONSTRAINT input_type_value
        CHECK(input_type IN ('unknown', 'source', 'lt_source', 'lt_gmpe',
                             'exposure', 'vulnerability')),
    -- Number of bytes in file
    size INTEGER NOT NULL DEFAULT 0,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;


-- An OpenQuake engine run started by the user
CREATE TABLE uiapi.oq_job (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    description VARCHAR NOT NULL,
    -- The full path of the location where the input files for the calculation
    -- engine reside. It is optional as long as the job has not been started.
    path VARCHAR UNIQUE CONSTRAINT job_path_value CHECK(
        ((status IN ('running', 'failed', 'succeeded') AND (path IS NOT NULL))
        OR (status = 'pending'))),
    -- One of:
    --      classical (Classical PSHA)
    --      event_based (Probabilistic event based)
    --      deterministic (Deterministic)
    -- Note: 'classical' and 'event_based' are both probabilistic methods
    job_type VARCHAR NOT NULL CONSTRAINT job_type_value
        CHECK(job_type IN ('classical', 'event_based', 'deterministic')),
    -- One of: pending, running, failed, succeeded
    status VARCHAR NOT NULL DEFAULT 'pending' CONSTRAINT job_status_value
        CHECK(status IN ('pending', 'running', 'failed', 'succeeded')),
    duration INTEGER NOT NULL DEFAULT 0,
    job_pid INTEGER NOT NULL DEFAULT 0,
    oq_params_id INTEGER NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;


-- The parameters needed for an OpenQuake engine run
CREATE TABLE uiapi.oq_params (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR NOT NULL CONSTRAINT job_type_value
        CHECK(job_type IN ('classical', 'event_based', 'deterministic')),
    upload_id INTEGER NOT NULL,
    region_grid_spacing float NOT NULL,
    min_magnitude float CONSTRAINT min_magnitude_set
        CHECK(
            ((job_type = 'deterministic') AND (min_magnitude IS NULL))
            OR ((job_type != 'deterministic') AND (min_magnitude IS NOT NULL))),
    investigation_time float CONSTRAINT investigation_time_set
        CHECK(
            ((job_type = 'deterministic') AND (investigation_time IS NULL))
            OR ((job_type != 'deterministic') AND (investigation_time IS NOT NULL))),
    -- One of:
    --      average (Average horizontal)
    --      gmroti50 (Average horizontal (GMRotI50))
    component VARCHAR NOT NULL CONSTRAINT component_value
        CHECK(component IN ('average', 'gmroti50')),
    -- Intensity measure type, one of:
    --      peak ground acceleration (pga)
    --      spectral acceleration (sa)
    --      peak ground velocity (pgv)
    --      peak ground displacement (pgd)
    imt VARCHAR NOT NULL CONSTRAINT imt_value
        CHECK(imt IN ('pga', 'sa', 'pgv', 'pgd')),
    period float CONSTRAINT period_is_set
        CHECK(((imt = 'sa') AND (period IS NOT NULL))
              OR ((imt != 'sa') AND (period IS NULL))),
    truncation_type VARCHAR NOT NULL CONSTRAINT truncation_type_value
        CHECK(truncation_type IN ('none', 'onesided', 'twosided')),
    truncation_level float NOT NULL,
    reference_vs30_value float NOT NULL,
    -- Intensity measure levels
    imls float[] CONSTRAINT imls_are_set
        CHECK(
            ((job_type = 'classical') AND (imls IS NOT NULL))
            OR ((job_type != 'classical') AND (imls IS NULL))),
    -- Probabilities of exceedence
    poes float[] CONSTRAINT poes_are_set
        CHECK(
            ((job_type = 'classical') AND (poes IS NOT NULL))
            OR ((job_type != 'classical') AND (poes IS NULL))),
    -- Number of logic tree samples
    realizations integer CONSTRAINT realizations_is_set
        CHECK(
            ((job_type = 'deterministic') AND (realizations IS NULL))
            OR ((job_type != 'deterministic') AND (realizations IS NOT NULL))),
    -- Number of seismicity histories
    histories integer CONSTRAINT histories_is_set
        CHECK(
            ((job_type = 'event_based') AND (histories IS NOT NULL))
            OR ((job_type != 'event_based') AND (histories IS NULL))),
    -- ground motion correlation flag
    gm_correlated boolean CONSTRAINT gm_correlated_is_set
        CHECK(
            ((job_type = 'classical') AND (gm_correlated IS NULL))
            OR ((job_type != 'classical') AND (gm_correlated IS NOT NULL))),
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'oq_params', 'region', 4326, 'POLYGON', 2);
ALTER TABLE uiapi.oq_params ALTER COLUMN region SET NOT NULL;


-- A single OpenQuake calculation engine output file.
CREATE TABLE uiapi.output (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    oq_job_id INTEGER NOT NULL,
    -- The full path of the output file on the server
    path VARCHAR NOT NULL UNIQUE,
    -- Output file type, one of:
    --      hazard_curve
    --      hazard_map
    --      loss_curve
    --      loss_map
    output_type VARCHAR NOT NULL CONSTRAINT output_type_value
        CHECK(output_type IN ('unknown', 'hazard_curve', 'hazard_map',
            'loss_curve', 'loss_map')),
    -- Number of bytes in file
    size INTEGER NOT NULL DEFAULT 0,
    -- The full path of the shapefile generated for a hazard or loss map.
    shapefile_path VARCHAR,
    -- The geonode URL of the shapefile generated for a hazard or loss map.
    shapefile_url VARCHAR,
    -- The min/max value is only needed for hazard/loss maps (for the
    -- generation of the relative color scale)
    min_value float,
    max_value float,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;


------------------------------------------------------------------------
-- Constraints (foreign keys etc.) go here
------------------------------------------------------------------------
ALTER TABLE admin.oq_user ADD CONSTRAINT admin_oq_user_organization_fk
FOREIGN KEY (organization_id) REFERENCES admin.organization(id) ON DELETE RESTRICT;

ALTER TABLE pshai.rupture ADD CONSTRAINT pshai_rupture_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.source ADD CONSTRAINT pshai_source_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.simple_fault ADD CONSTRAINT pshai_simple_fault_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.complex_fault ADD CONSTRAINT pshai_complex_fault_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.fault_edge ADD CONSTRAINT pshai_fault_edge_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.mfd_evd ADD CONSTRAINT pshai_mfd_evd_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.mfd_tgr ADD CONSTRAINT pshai_mfd_tgr_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.r_depth_distr ADD CONSTRAINT pshai_r_depth_distr_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.focal_mechanism ADD CONSTRAINT pshai_focal_mechanism_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.r_rate_mdl ADD CONSTRAINT pshai_r_rate_mdl_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.complex_fault ADD CONSTRAINT pshai_complex_fault_fault_edge_fk
FOREIGN KEY (fault_edge_id) REFERENCES pshai.fault_edge(id) ON DELETE RESTRICT;

ALTER TABLE pshai.r_rate_mdl ADD CONSTRAINT pshai_r_rate_mdl_mfd_tgr_fk
FOREIGN KEY (mfd_tgr_id) REFERENCES pshai.mfd_tgr(id) ON DELETE RESTRICT;

ALTER TABLE pshai.r_rate_mdl ADD CONSTRAINT pshai_r_rate_mdl_mfd_evd_fk
FOREIGN KEY (mfd_evd_id) REFERENCES pshai.mfd_evd(id) ON DELETE RESTRICT;

ALTER TABLE pshai.r_rate_mdl ADD CONSTRAINT pshai_r_rate_mdl_focal_mechanism_fk
FOREIGN KEY (focal_mechanism_id) REFERENCES pshai.focal_mechanism(id) ON DELETE RESTRICT;

ALTER TABLE pshai.r_rate_mdl ADD CONSTRAINT pshai_r_rate_mdl_source_fk
FOREIGN KEY (source_id) REFERENCES pshai.source(id) ON DELETE RESTRICT;

ALTER TABLE pshai.simple_fault ADD CONSTRAINT pshai_simple_fault_mfd_tgr_fk
FOREIGN KEY (mfd_tgr_id) REFERENCES pshai.mfd_tgr(id) ON DELETE RESTRICT;

ALTER TABLE pshai.simple_fault ADD CONSTRAINT pshai_simple_fault_mfd_evd_fk
FOREIGN KEY (mfd_evd_id) REFERENCES pshai.mfd_evd(id) ON DELETE RESTRICT;

ALTER TABLE pshai.complex_fault ADD CONSTRAINT pshai_complex_fault_mfd_tgr_fk
FOREIGN KEY (mfd_tgr_id) REFERENCES pshai.mfd_tgr(id) ON DELETE RESTRICT;

ALTER TABLE pshai.complex_fault ADD CONSTRAINT pshai_complex_fault_mfd_evd_fk
FOREIGN KEY (mfd_evd_id) REFERENCES pshai.mfd_evd(id) ON DELETE RESTRICT;

ALTER TABLE pshai.source ADD CONSTRAINT pshai_source_simple_fault_fk
FOREIGN KEY (simple_fault_id) REFERENCES pshai.simple_fault(id) ON DELETE RESTRICT;

ALTER TABLE pshai.source ADD CONSTRAINT pshai_source_complex_fault_fk
FOREIGN KEY (complex_fault_id) REFERENCES pshai.complex_fault(id) ON DELETE RESTRICT;

ALTER TABLE pshai.source ADD CONSTRAINT pshai_source_r_depth_distr_fk
FOREIGN KEY (r_depth_distr_id) REFERENCES pshai.r_depth_distr(id) ON DELETE RESTRICT;

ALTER TABLE pshai.source ADD CONSTRAINT pshai_source_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE RESTRICT;

ALTER TABLE pshai.rupture ADD CONSTRAINT pshai_rupture_simple_fault_fk
FOREIGN KEY (simple_fault_id) REFERENCES pshai.simple_fault(id) ON DELETE RESTRICT;

ALTER TABLE pshai.rupture ADD CONSTRAINT pshai_rupture_complex_fault_fk
FOREIGN KEY (complex_fault_id) REFERENCES pshai.complex_fault(id) ON DELETE RESTRICT;

ALTER TABLE pshai.rupture ADD CONSTRAINT pshai_rupture_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE RESTRICT;

CREATE TRIGGER pshai_rupture_before_insert_update_trig
BEFORE INSERT OR UPDATE ON pshai.rupture
FOR EACH ROW EXECUTE PROCEDURE check_rupture_sources();

CREATE TRIGGER pshai_source_before_insert_update_trig
BEFORE INSERT OR UPDATE ON pshai.source
FOR EACH ROW EXECUTE PROCEDURE check_source_sources();

CREATE TRIGGER pshai_r_rate_mdl_before_insert_update_trig
BEFORE INSERT OR UPDATE ON pshai.r_rate_mdl
FOR EACH ROW EXECUTE PROCEDURE check_only_one_mfd_set();

CREATE TRIGGER pshai_simple_fault_before_insert_update_trig
BEFORE INSERT OR UPDATE ON pshai.simple_fault
FOR EACH ROW EXECUTE PROCEDURE check_only_one_mfd_set();

CREATE TRIGGER pshai_complex_fault_before_insert_update_trig
BEFORE INSERT OR UPDATE ON pshai.complex_fault
FOR EACH ROW EXECUTE PROCEDURE check_only_one_mfd_set();

ALTER TABLE eqcat.catalog ADD CONSTRAINT eqcat_catalog_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE eqcat.catalog ADD CONSTRAINT eqcat_catalog_magnitude_fk
FOREIGN KEY (magnitude_id) REFERENCES eqcat.magnitude(id) ON DELETE RESTRICT;

ALTER TABLE eqcat.catalog ADD CONSTRAINT eqcat_catalog_surface_fk
FOREIGN KEY (surface_id) REFERENCES eqcat.surface(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.oq_job ADD CONSTRAINT uiapi_oq_job_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.oq_job ADD CONSTRAINT uiapi_oq_job_oq_params_fk
FOREIGN KEY (oq_params_id) REFERENCES uiapi.oq_params(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.upload ADD CONSTRAINT uiapi_upload_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.oq_params ADD CONSTRAINT uiapi_oq_params_upload_fk
FOREIGN KEY (upload_id) REFERENCES uiapi.upload(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.input ADD CONSTRAINT uiapi_input_upload_fk
FOREIGN KEY (upload_id) REFERENCES uiapi.upload(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.input ADD CONSTRAINT uiapi_input_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.output ADD CONSTRAINT uiapi_output_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.output ADD CONSTRAINT uiapi_output_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

CREATE TRIGGER eqcat_magnitude_before_insert_update_trig
BEFORE INSERT OR UPDATE ON eqcat.magnitude
FOR EACH ROW EXECUTE PROCEDURE check_magnitude_data();

CREATE TRIGGER admin_organization_refresh_last_update_trig BEFORE UPDATE ON admin.organization FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER admin_oq_user_refresh_last_update_trig BEFORE UPDATE ON admin.oq_user FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER eqcat_catalog_refresh_last_update_trig BEFORE UPDATE ON eqcat.catalog FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER eqcat_surface_refresh_last_update_trig BEFORE UPDATE ON eqcat.surface FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER pshai_fault_edge_refresh_last_update_trig BEFORE UPDATE ON pshai.fault_edge FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER pshai_mfd_evd_refresh_last_update_trig BEFORE UPDATE ON pshai.mfd_evd FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER pshai_mfd_tgr_refresh_last_update_trig BEFORE UPDATE ON pshai.mfd_tgr FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER pshai_r_depth_distr_refresh_last_update_trig BEFORE UPDATE ON pshai.r_depth_distr FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER pshai_focal_mechanism_refresh_last_update_trig BEFORE UPDATE ON pshai.focal_mechanism FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();
