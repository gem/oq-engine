/*
  OpenQuake database schema definitions.

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


------------------------------------------------------------------------
-- Name space definitions go here
------------------------------------------------------------------------
CREATE SCHEMA admin;
CREATE SCHEMA eqcat;
CREATE SCHEMA hzrdi;
CREATE SCHEMA hzrdr;
CREATE SCHEMA oqmif;
CREATE SCHEMA riski;
CREATE SCHEMA riskr;
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
CREATE TABLE hzrdi.rupture (
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
) TABLESPACE hzrdi_ts;
SELECT AddGeometryColumn('hzrdi', 'rupture', 'point', 4326, 'POINT', 3);


-- source
CREATE TABLE hzrdi.source (
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
) TABLESPACE hzrdi_ts;
SELECT AddGeometryColumn('hzrdi', 'source', 'point', 4326, 'POINT', 2);
SELECT AddGeometryColumn('hzrdi', 'source', 'area', 4326, 'POLYGON', 2);


-- Simple fault geometry
CREATE TABLE hzrdi.simple_fault (
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
) TABLESPACE hzrdi_ts;
SELECT AddGeometryColumn('hzrdi', 'simple_fault', 'edge', 4326, 'LINESTRING', 3);
ALTER TABLE hzrdi.simple_fault ALTER COLUMN edge SET NOT NULL;
SELECT AddGeometryColumn('hzrdi', 'simple_fault', 'outline', 4326, 'POLYGON', 3);

-- Magnitude frequency distribution, Evenly discretized
CREATE TABLE hzrdi.mfd_evd (
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
) TABLESPACE hzrdi_ts;


-- Magnitude frequency distribution, Truncated Gutenberg Richter
CREATE TABLE hzrdi.mfd_tgr (
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
) TABLESPACE hzrdi_ts;


-- simple source view, needed for Opengeo server integration
CREATE VIEW hzrdi.simple_source AS
SELECT
    -- Columns specific to hzrdi.source
    hzrdi.source.id,
    hzrdi.source.owner_id,
    hzrdi.source.input_id,
    hzrdi.source.gid,
    hzrdi.source.name,
    hzrdi.source.description,
    hzrdi.source.si_type,
    hzrdi.source.tectonic_region,
    hzrdi.source.rake,

    -- Columns specific to hzrdi.simple_fault
    hzrdi.simple_fault.dip,
    hzrdi.simple_fault.upper_depth,
    hzrdi.simple_fault.lower_depth,
    hzrdi.simple_fault.edge,
    hzrdi.simple_fault.outline,

    CASE WHEN mfd_evd_id IS NOT NULL THEN 'evd' ELSE 'tgr' END AS mfd_type,

    -- Common MFD columns, only one of each will be not NULL.
    COALESCE(hzrdi.mfd_evd.magnitude_type, hzrdi.mfd_tgr.magnitude_type)
        AS magnitude_type,
    COALESCE(hzrdi.mfd_evd.min_val, hzrdi.mfd_tgr.min_val) AS min_val,
    COALESCE(hzrdi.mfd_evd.max_val, hzrdi.mfd_tgr.max_val) AS max_val,
    COALESCE(hzrdi.mfd_evd.total_cumulative_rate,
             hzrdi.mfd_tgr.total_cumulative_rate) AS total_cumulative_rate,
    COALESCE(hzrdi.mfd_evd.total_moment_rate,
             hzrdi.mfd_tgr.total_moment_rate) AS total_moment_rate,

    -- Columns specific to hzrdi.mfd_evd
    hzrdi.mfd_evd.bin_size AS evd_bin_size,
    hzrdi.mfd_evd.mfd_values AS evd_values,

    -- Columns specific to hzrdi.mfd_tgr
    hzrdi.mfd_tgr.a_val AS tgr_a_val,
    hzrdi.mfd_tgr.b_val AS tgr_b_val
FROM
    hzrdi.source
JOIN hzrdi.simple_fault ON hzrdi.simple_fault.id = hzrdi.source.simple_fault_id
LEFT OUTER JOIN hzrdi.mfd_evd ON
    hzrdi.mfd_evd.id = hzrdi.simple_fault.mfd_evd_id
LEFT OUTER JOIN hzrdi.mfd_tgr ON
    hzrdi.mfd_tgr.id  = hzrdi.simple_fault.mfd_tgr_id;


-- simple rupture view, needed for Opengeo server integration
CREATE VIEW hzrdi.simple_rupture (
    id, owner_id, input_id, gid, name, description, si_type, tectonic_region,
    rake, magnitude, magnitude_type, edge, fault_outline) AS
SELECT
    rup.id, rup.owner_id, rup.input_id, rup.gid, rup.name, rup.description,
    rup.si_type, rup.tectonic_region, rup.rake, rup.magnitude,
    rup.magnitude_type, sfault.edge, sfault.outline
FROM
    hzrdi.rupture rup, hzrdi.simple_fault sfault
WHERE
    rup.si_type = 'simple'
    AND rup.simple_fault_id = sfault.id;


-- Complex fault geometry
CREATE TABLE hzrdi.complex_fault (
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
) TABLESPACE hzrdi_ts;
SELECT AddGeometryColumn('hzrdi', 'complex_fault', 'outline', 4326, 'POLYGON', 3);


-- Fault edge
CREATE TABLE hzrdi.fault_edge (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE hzrdi_ts;
SELECT AddGeometryColumn('hzrdi', 'fault_edge', 'top', 4326, 'LINESTRING', 3);
SELECT AddGeometryColumn('hzrdi', 'fault_edge', 'bottom', 4326, 'LINESTRING', 3);
ALTER TABLE hzrdi.fault_edge ALTER COLUMN top SET NOT NULL;
ALTER TABLE hzrdi.fault_edge ALTER COLUMN bottom SET NOT NULL;


-- complex source view, needed for Opengeo server integration
CREATE VIEW hzrdi.complex_source (
    id, owner_id, input_id, gid, name, description, si_type, tectonic_region,
    rake, top_edge, bottom_edge, fault_outline) AS
SELECT
    src.id, src.owner_id, src.input_id, src.gid, src.name, src.description,
    src.si_type, src.tectonic_region, src.rake, fedge.top, fedge.bottom,
    cfault.outline
FROM
    hzrdi.source src, hzrdi.complex_fault cfault, hzrdi.fault_edge fedge
WHERE
    src.si_type = 'complex'
    AND src.complex_fault_id = cfault.id AND cfault.fault_edge_id = fedge.id;


-- complex rupture view, needed for Opengeo server integration
CREATE VIEW hzrdi.complex_rupture (
    id, owner_id, input_id, gid, name, description, si_type, tectonic_region,
    rake, magnitude, magnitude_type, top_edge, bottom_edge, fault_outline) AS
SELECT
    rup.id, rup.owner_id, rup.input_id, rup.gid, rup.name, rup.description,
    rup.si_type, rup.tectonic_region, rup.rake, rup.magnitude,
    rup.magnitude_type, fedge.top, fedge.bottom, cfault.outline
FROM
    hzrdi.rupture rup, hzrdi.complex_fault cfault, hzrdi.fault_edge fedge
WHERE
    rup.si_type = 'complex'
    AND rup.complex_fault_id = cfault.id AND cfault.fault_edge_id = fedge.id;


-- Rupture depth distribution
CREATE TABLE hzrdi.r_depth_distr (
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
) TABLESPACE hzrdi_ts;


-- Rupture rate model
CREATE TABLE hzrdi.r_rate_mdl (
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
) TABLESPACE hzrdi_ts;


-- Holds strike, dip and rake values with the respective constraints.
CREATE TABLE hzrdi.focal_mechanism (
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
) TABLESPACE hzrdi_ts;


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


-- Set of input files for an OpenQuake job
CREATE TABLE uiapi.input_set (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    upload_id INTEGER,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;


-- A single OpenQuake input file uploaded by the user
CREATE TABLE uiapi.input (
    id SERIAL PRIMARY KEY,
    input_set_id INTEGER NOT NULL,
    -- The full path of the input file on the server
    path VARCHAR NOT NULL,
    -- Input file type, one of:
    --      source model file (source)
    --      source logic tree (lt_source)
    --      GMPE logic tree (lt_gmpe)
    --      exposure file (exposure)
    --      vulnerability file (vulnerability)
    --      rupture file (rupture)
    input_type VARCHAR NOT NULL CONSTRAINT input_type_value
        CHECK(input_type IN ('unknown', 'source', 'lt_source', 'lt_gmpe',
                             'exposure', 'vulnerability', 'rupture')),
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
    -- engine reside. This is used internally by openquake-server, can probably
    -- be removed (see https://github.com/gem/openquake-server/issues/55)
    path VARCHAR UNIQUE,
    -- One of:
    --      classical (Classical PSHA)
    --      event_based (Probabilistic event based)
    --      deterministic (Deterministic)
    --      disaggregation (Hazard only)
    -- Note: 'classical' and 'event_based' are both probabilistic methods
    job_type VARCHAR NOT NULL CONSTRAINT job_type_value
        CHECK(job_type IN ('classical', 'event_based', 'deterministic',
                           'disaggregation')),
    -- One of: pending, running, failed, succeeded
    status VARCHAR NOT NULL DEFAULT 'pending' CONSTRAINT job_status_value
        CHECK(status IN ('pending', 'running', 'failed', 'succeeded')),
    duration INTEGER NOT NULL DEFAULT 0,
    job_pid INTEGER NOT NULL DEFAULT 0,
    supervisor_pid INTEGER NOT NULL DEFAULT 0,
    oq_params_id INTEGER NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;


-- Tracks various job statistics
CREATE TABLE uiapi.job_stats (
    id SERIAL PRIMARY KEY,
    oq_job_id INTEGER NOT NULL,
    start_time timestamp with time zone,
    stop_time timestamp with time zone,
    -- The number of total sites in the calculation
    num_sites INTEGER NOT NULL
) TABLESPACE uiapi_ts;


-- The parameters needed for an OpenQuake engine run
CREATE TABLE uiapi.oq_params (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR NOT NULL CONSTRAINT job_type_value
        CHECK(job_type IN ('classical', 'event_based', 'deterministic',
                           'disaggregation')),
    input_set_id INTEGER NOT NULL,
    region_grid_spacing float,
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
    damping float CONSTRAINT damping_is_set
        CHECK(((imt = 'sa') AND (damping IS NOT NULL))
              OR ((imt != 'sa') AND (damping IS NULL))),
    truncation_type VARCHAR NOT NULL CONSTRAINT truncation_type_value
        CHECK(truncation_type IN ('none', 'onesided', 'twosided')),
    truncation_level float NOT NULL DEFAULT 3.0,
    reference_vs30_value float NOT NULL,
    -- Intensity measure levels
    imls float[] CONSTRAINT imls_are_set
        CHECK(
            ((job_type in ('classical', 'event_based', 'disaggregation'))
            AND (imls IS NOT NULL))
            OR ((job_type = 'deterministic') AND (imls IS NULL))),
    -- Probabilities of exceedence
    poes float[] CONSTRAINT poes_are_set
        CHECK(
            ((job_type IN ('classical', 'disaggregation')) AND (poes IS NOT NULL))
            OR ((job_type IN ('event_based', 'deterministic')) AND (poes IS NULL))),
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
            ((job_type IN ('classical', 'disaggregation')) AND (gm_correlated IS NULL))
            OR ((job_type IN ('event_based', 'deterministic')) AND (gm_correlated IS NOT NULL))),
    gmf_calculation_number integer CONSTRAINT gmf_calculation_number_is_set
        CHECK(
            ((job_type = 'deterministic')
             AND (gmf_calculation_number IS NOT NULL)
             AND (realizations > 0))
            OR
            ((job_type != 'deterministic')
             AND (gmf_calculation_number IS NULL))),
    rupture_surface_discretization float
        CONSTRAINT rupture_surface_discretization_is_set
        CHECK(
            ((job_type = 'deterministic')
             AND (rupture_surface_discretization IS NOT NULL)
             AND (rupture_surface_discretization > 0))
            OR
            ((job_type != 'deterministic')
             AND (rupture_surface_discretization IS NULL))),

    aggregate_loss_curve boolean,
    area_source_discretization float
        CONSTRAINT area_source_discretization_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (area_source_discretization IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (area_source_discretization IS NULL))),
    area_source_magnitude_scaling_relationship VARCHAR
        CONSTRAINT area_source_magnitude_scaling_relationship_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (area_source_magnitude_scaling_relationship IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (area_source_magnitude_scaling_relationship IS NULL))),
    compute_mean_hazard_curve boolean
        CONSTRAINT compute_mean_hazard_curve_is_set
        CHECK(
            ((job_type = 'classical')
             AND (compute_mean_hazard_curve IS NOT NULL))
            OR
            ((job_type IN ('deterministic', 'event_based', 'disaggregation'))
             AND (compute_mean_hazard_curve IS NULL))),
    conditional_loss_poe float[],
    fault_magnitude_scaling_relationship VARCHAR
        CONSTRAINT fault_magnitude_scaling_relationship_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (fault_magnitude_scaling_relationship IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (fault_magnitude_scaling_relationship IS NULL))),
    fault_magnitude_scaling_sigma float
        CONSTRAINT fault_magnitude_scaling_sigma_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (fault_magnitude_scaling_sigma IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (fault_magnitude_scaling_sigma IS NULL))),
    fault_rupture_offset float
        CONSTRAINT fault_rupture_offset_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (fault_rupture_offset IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (fault_rupture_offset IS NULL))),
    fault_surface_discretization float
        CONSTRAINT fault_surface_discretization_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (fault_surface_discretization IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (fault_surface_discretization IS NULL))),
    gmf_random_seed integer
        CONSTRAINT gmf_random_seed_is_set
        CHECK(
            (job_type IN ('deterministic', 'event_based'))
            OR
            ((job_type IN ('classical', 'disaggregation'))
             AND (gmf_random_seed IS NULL))),
    gmpe_lt_random_seed integer
        CONSTRAINT gmpe_lt_random_seed_is_set
        CHECK(
            (job_type IN ('classical', 'event_based', 'disaggregation'))
            OR
            ((job_type = 'deterministic')
             AND (gmpe_lt_random_seed IS NULL))),
    gmpe_model_name VARCHAR,
    grid_source_magnitude_scaling_relationship VARCHAR,
    include_area_sources boolean
        CONSTRAINT include_area_sources_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (include_area_sources IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (include_area_sources IS NULL))),
    include_fault_source boolean
        CONSTRAINT include_fault_source_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (include_fault_source IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (include_fault_source IS NULL))),
    include_grid_sources boolean
        CONSTRAINT include_grid_sources_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (include_grid_sources IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (include_grid_sources IS NULL))),
    include_subduction_fault_source boolean
        CONSTRAINT include_subduction_fault_source_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (include_subduction_fault_source IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (include_subduction_fault_source IS NULL))),
    loss_curves_output_prefix VARCHAR,
    maximum_distance VARCHAR
        CONSTRAINT maximum_distance_is_set
        CHECK(
            ((job_type IN ('classical', 'disaggregation'))
             AND (maximum_distance IS NOT NULL))
            OR
            ((job_type IN ('deterministic', 'event_based'))
             AND (maximum_distance IS NULL))),
    quantile_levels float[]
        CONSTRAINT quantile_levels_is_set
        CHECK(
            ((job_type = 'classical')
             AND (quantile_levels IS NOT NULL))
            OR
            ((job_type IN ('deterministic', 'event_based', 'disaggregation'))
             AND (quantile_levels IS NULL))),
    reference_depth_to_2pt5km_per_sec_param float,
    risk_cell_size float,
    rupture_aspect_ratio float
        CONSTRAINT rupture_aspect_ratio_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (rupture_aspect_ratio IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (rupture_aspect_ratio IS NULL))),
    -- Rupture floating type, one of:
    --     Only along strike ( rupture full DDW) (alongstrike)
    --     Along strike and down dip (downdip)
    --     Along strike & centered down dip (centereddowndip)
    rupture_floating_type VARCHAR
        CONSTRAINT rupture_floating_type_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (rupture_floating_type IN ('alongstrike', 'downdip', 'centereddowndip')))
            OR
            ((job_type = 'deterministic')
             AND (rupture_floating_type IS NULL))),
    -- Sadigh site type, one of:
    --     Rock (rock)
    --     Deep-Soil (deepsoil)
    sadigh_site_type VARCHAR CONSTRAINT sadigh_site_type_value
        CHECK(sadigh_site_type IS NULL
              OR sadigh_site_type IN ('rock', 'deepsoil')),
    source_model_lt_random_seed integer
        CONSTRAINT source_model_lt_random_seed_is_set
        CHECK(
            (job_type IN ('classical', 'event_based', 'disaggregation'))
            OR
            ((job_type = 'deterministic')
             AND (source_model_lt_random_seed IS NULL))),
    -- Standard deviation, one of:
    --     Total (total)
    --     Inter-Event (interevent)
    --     Intra-Event (intraevent)
    --     None (zero) (zero)
    --     Total (Mag Dependent) (total_mag_dependent)
    --     Total (PGA Dependent) (total_pga_dependent)
    --     Intra-Event (Mag Dependent) (intraevent_mag_dependent)
    standard_deviation_type VARCHAR
        CONSTRAINT standard_deviation_type_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (standard_deviation_type IN ('total', 'interevent', 'intraevent', 'zero', 'total_mag_dependent', 'total_pga_dependent', 'intraevent_mag_dependent')))
            OR
            ((job_type = 'deterministic')
             AND (standard_deviation_type IS NULL))),
    subduction_fault_magnitude_scaling_relationship VARCHAR
        CONSTRAINT subduction_fault_magnitude_scaling_relationship_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (subduction_fault_magnitude_scaling_relationship IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (subduction_fault_magnitude_scaling_relationship IS NULL))),
    subduction_fault_magnitude_scaling_sigma float
        CONSTRAINT subduction_fault_magnitude_scaling_sigma_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (subduction_fault_magnitude_scaling_sigma IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (subduction_fault_magnitude_scaling_sigma IS NULL))),
    subduction_fault_rupture_offset float
        CONSTRAINT subduction_fault_rupture_offset_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (subduction_fault_rupture_offset IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (subduction_fault_rupture_offset IS NULL))),
    subduction_fault_surface_discretization float
        CONSTRAINT subduction_fault_surface_discretization_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (subduction_fault_surface_discretization IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (subduction_fault_surface_discretization IS NULL))),
    subduction_rupture_aspect_ratio float
        CONSTRAINT subduction_rupture_aspect_ratio_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (subduction_rupture_aspect_ratio IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (subduction_rupture_aspect_ratio IS NULL))),
    -- Rupture floating type, one of:
    --     Only along strike ( rupture full DDW) (alongstrike)
    --     Along strike and down dip (downdip)
    --     Along strike & centered down dip (centereddowndip)
    subduction_rupture_floating_type VARCHAR
        CONSTRAINT subduction_rupture_floating_type_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (subduction_rupture_floating_type IN ('alongstrike', 'downdip', 'centereddowndip')))
            OR
            ((job_type = 'deterministic')
             AND (subduction_rupture_floating_type IS NULL))),
    -- Source as, one of:
    --     Point Sources (pointsources)
    --     Line Sources (random or given strike) (linesources)
    --     Cross Hair Line Sources (crosshairsources)
    --     16 Spoked Line Sources (16spokedsources)
    treat_area_source_as VARCHAR
        CONSTRAINT treat_area_source_as_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (treat_area_source_as IN ('pointsources', 'linesources', 'crosshairsources', '16spokedsources')))
            OR
            ((job_type = 'deterministic')
             AND (treat_area_source_as IS NULL))),
    treat_grid_source_as VARCHAR
        CONSTRAINT treat_grid_source_as_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (treat_grid_source_as IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (treat_grid_source_as IS NULL))),
    width_of_mfd_bin float
        CONSTRAINT width_of_mfd_bin_is_set
        CHECK(
            ((job_type IN ('classical', 'event_based', 'disaggregation'))
             AND (width_of_mfd_bin IS NOT NULL))
            OR
            ((job_type = 'deterministic')
             AND (width_of_mfd_bin IS NULL))),
    lat_bin_limits float[]
        CONSTRAINT lat_bin_limits_valid
        CHECK(
            (((job_type = 'disaggregation')
            AND (lat_bin_limits IS NOT NULL)
            AND (-90 <= all(lat_bin_limits))
            AND (90 >= all(lat_bin_limits))
            OR
            ((job_type != 'disaggregation')
            AND (lat_bin_limits IS NULL))))),
    lon_bin_limits float[]
        CONSTRAINT lon_bin_limits_valid
        CHECK(
            (((job_type = 'disaggregation')
            AND (lon_bin_limits IS NOT NULL)
            AND (-180 <= all(lon_bin_limits))
            AND (180 >= all(lon_bin_limits))
            OR
            ((job_type != 'disaggregation')
            AND (lon_bin_limits IS NULL))))),
    mag_bin_limits float[]
        CONSTRAINT mag_bin_limits_is_set
        CHECK(
            ((job_type = 'disaggregation')
            AND (mag_bin_limits IS NOT NULL))
            OR
            ((job_type != 'disaggregation')
            AND (mag_bin_limits IS NULL))),
    epsilon_bin_limits float[]
        CONSTRAINT epsilon_bin_limits_is_set
        CHECK(
            ((job_type = 'disaggregation')
            AND (epsilon_bin_limits IS NOT NULL))
            OR
            ((job_type != 'disaggregation')
            AND (epsilon_bin_limits IS NULL))),
    distance_bin_limits float[]
        CONSTRAINT distance_bin_limits_is_set
        CHECK(
            ((job_type = 'disaggregation')
            AND (distance_bin_limits IS NOT NULL))
            OR
            ((job_type != 'disaggregation')
            AND (distance_bin_limits IS NULL))),
    -- For disaggregation results, choose any (at least 1) of the following:
    --      magpmf (Magnitude Probability Mass Function)
    --      distpmf (Distance PMF)
    --      trtpmf (Tectonic Region Type PMF)
    --      magdistpmf (Magnitude-Distance PMF)
    --      magdistepspmf (Magnitude-Distance-Epsilon PMF)
    --      latlonpmf (Latitude-Longitude PMF)
    --      latlonmagpmf (Latitude-Longitude-Magnitude PMF)
    --      latlonmagepspmf (Latitude-Longitude-Magnitude-Epsilon PMF)
    --      magtrtpmf (Magnitude-Tectonic Region Type PMF)
    --      latlontrtpmf (Latitude-Longitude-Tectonic Region Type PMF)
    --      fulldisaggmatrix (The full disaggregation matrix; includes
    --          Lat, Lon, Magnitude, Epsilon, and Tectonic Region Type)
    disagg_results VARCHAR[]
        CONSTRAINT disagg_results_valid
        CHECK(
            (((job_type = 'disaggregation')
            AND (disagg_results IS NOT NULL)
            AND (disagg_results <@ ARRAY['magpmf', 'distpmf', 'trtpmf',
                                         'magdistpmf', 'magdistepspmf',
                                         'latlonpmf', 'latlonmagpmf',
                                         'latlonmagepspmf',
                                         'magtrtpmf', 'latlontrtpmf',
                                         'fulldisaggmatrix']::VARCHAR[]))
            OR
            ((job_type != 'disaggregation')
            AND (disagg_results IS NULL)))),
    depth_to_1pt_0km_per_sec float NOT NULL DEFAULT 100.0
        CONSTRAINT depth_to_1pt_0km_per_sec_above_zero
        CHECK(depth_to_1pt_0km_per_sec > 0.0),
    vs30_type VARCHAR NOT NULL DEFAULT 'measured' CONSTRAINT vs30_type_value
        CHECK(vs30_type IN ('measured', 'inferred')),
    -- timestamp
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'oq_params', 'region', 4326, 'POLYGON', 2);
SELECT AddGeometryColumn('uiapi', 'oq_params', 'sites', 4326, 'MULTIPOINT', 2);
-- Params can either contain a site list ('sites') or
-- region + region_grid_spacing, but not both.
ALTER TABLE uiapi.oq_params ADD CONSTRAINT oq_params_geometry CHECK(
    ((region IS NOT NULL) AND (region_grid_spacing IS NOT NULL)
        AND (sites IS NULL))
    OR ((region IS NULL) AND (region_grid_spacing IS NULL)
        AND (sites IS NOT NULL)));


-- A single OpenQuake calculation engine output. The data may reside in a file
-- or in the database.
CREATE TABLE uiapi.output (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    oq_job_id INTEGER NOT NULL,
    -- The full path of the output file on the server, optional and only set
    -- for outputs with NRML/XML files.
    path VARCHAR UNIQUE,
    -- The GUI display name to be used for this output.
    display_name VARCHAR NOT NULL,
    -- True if the output's data resides in the database and not in a file.
    db_backed boolean NOT NULL DEFAULT FALSE,
    -- Output type, one of:
    --      hazard_curve
    --      hazard_map
    --      gmf
    --      loss_curve
    --      loss_map
    --      collapse_map
    --      bcr_distribution
    output_type VARCHAR NOT NULL CONSTRAINT output_type_value
        CHECK(output_type IN ('unknown', 'hazard_curve', 'hazard_map',
            'gmf', 'loss_curve', 'loss_map', 'collapse_map',
            'bcr_distribution')),
    -- Number of bytes in file
    size INTEGER NOT NULL DEFAULT 0,
    -- The full path of the shapefile generated for a hazard or loss map
    -- (optional).
    shapefile_path VARCHAR,
    -- The min/max value is only needed for hazard/loss maps (for the
    -- generation of the relative color scale)
    min_value float,
    max_value float,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;


-- A place to store error information in the case of a job failure.
CREATE TABLE uiapi.error_msg (
    id SERIAL PRIMARY KEY,
    oq_job_id INTEGER NOT NULL,
    -- Summary of the error message.
    brief VARCHAR NOT NULL,
    -- The full error message.
    detailed VARCHAR NOT NULL
) TABLESPACE uiapi_ts;


-- Hazard map header
CREATE TABLE hzrdr.hazard_map (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    poe float NOT NULL,
    -- Statistic type, one of:
    --      mean
    --      quantile
    statistic_type VARCHAR CONSTRAINT statistic_type_value
        CHECK(statistic_type IN ('mean', 'quantile')),
    -- Quantile value (only for "quantile" statistics)
    quantile float CONSTRAINT quantile_value
        CHECK(
            ((statistic_type = 'quantile') AND (quantile IS NOT NULL))
            OR (((statistic_type <> 'quantile') AND (quantile IS NULL))))
) TABLESPACE hzrdr_ts;


-- Hazard map data.
CREATE TABLE hzrdr.hazard_map_data (
    id SERIAL PRIMARY KEY,
    hazard_map_id INTEGER NOT NULL,
    value float NOT NULL
) TABLESPACE hzrdr_ts;
SELECT AddGeometryColumn('hzrdr', 'hazard_map_data', 'location', 4326, 'POINT', 2);
ALTER TABLE hzrdr.hazard_map_data ALTER COLUMN location SET NOT NULL;


-- Hazard curve data.
CREATE TABLE hzrdr.hazard_curve (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    -- Realization reference string
    end_branch_label VARCHAR CONSTRAINT end_branch_label_value
        CHECK(
            ((end_branch_label IS NULL) AND (statistic_type IS NOT NULL))
            OR ((end_branch_label IS NOT NULL) AND (statistic_type IS NULL))),
    -- Statistic type, one of:
    --      mean
    --      median
    --      quantile
    statistic_type VARCHAR CONSTRAINT statistic_type_value
        CHECK(statistic_type IS NULL OR
              statistic_type IN ('mean', 'median', 'quantile')),
    -- Quantile value (only for "quantile" statistics)
    quantile float CONSTRAINT quantile_value
        CHECK(
            ((statistic_type = 'quantile') AND (quantile IS NOT NULL))
            OR (((statistic_type <> 'quantile') AND (quantile IS NULL))))
) TABLESPACE hzrdr_ts;


-- Hazard curve node data.
CREATE TABLE hzrdr.hazard_curve_data (
    id SERIAL PRIMARY KEY,
    hazard_curve_id INTEGER NOT NULL,
    -- Probabilities of exceedence
    poes float[] NOT NULL
) TABLESPACE hzrdr_ts;
SELECT AddGeometryColumn('hzrdr', 'hazard_curve_data', 'location', 4326, 'POINT', 2);
ALTER TABLE hzrdr.hazard_curve_data ALTER COLUMN location SET NOT NULL;


-- GMF data.
CREATE TABLE hzrdr.gmf_data (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    -- Ground motion value
    ground_motion float NOT NULL
) TABLESPACE hzrdr_ts;
SELECT AddGeometryColumn('hzrdr', 'gmf_data', 'location', 4326, 'POINT', 2);
ALTER TABLE hzrdr.gmf_data ALTER COLUMN location SET NOT NULL;


-- Loss map data.

CREATE TABLE riskr.loss_map (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    deterministic BOOLEAN NOT NULL,
    loss_map_ref VARCHAR,
    end_branch_label VARCHAR,
    category VARCHAR,
    unit VARCHAR, -- e.g. USD, EUR
    timespan float CONSTRAINT valid_timespan
        CHECK (timespan > 0.0),
    -- poe is significant only for non-deterministic calculations
    poe float CONSTRAINT valid_poe
        CHECK ((NOT deterministic AND (poe >= 0.0) AND (poe <= 1.0))
               OR (deterministic AND poe IS NULL))
) TABLESPACE riskr_ts;

CREATE TABLE riskr.loss_map_data (
    id SERIAL PRIMARY KEY,
    loss_map_id INTEGER NOT NULL, -- FK to loss_map.id
    asset_ref VARCHAR NOT NULL,
    value float NOT NULL,
    -- for non-deterministic calculations std_dev is 0
    std_dev float NOT NULL DEFAULT 0.0
) TABLESPACE riskr_ts;
SELECT AddGeometryColumn('riskr', 'loss_map_data', 'location', 4326, 'POINT', 2);
ALTER TABLE riskr.loss_map_data ALTER COLUMN location SET NOT NULL;


-- Loss curve.
CREATE TABLE riskr.loss_curve (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    aggregate BOOLEAN NOT NULL DEFAULT false,

    end_branch_label VARCHAR,
    category VARCHAR,
    unit VARCHAR -- e.g. EUR, USD
) TABLESPACE riskr_ts;


-- Loss curve data. Holds the asset, its position and value plus the calculated
-- curve.
CREATE TABLE riskr.loss_curve_data (
    id SERIAL PRIMARY KEY,
    loss_curve_id INTEGER NOT NULL,

    asset_ref VARCHAR NOT NULL,
    losses float[] NOT NULL CONSTRAINT non_negative_losses
        CHECK (0 <= ALL(losses)),
    -- Probabilities of exceedence
    poes float[] NOT NULL
) TABLESPACE riskr_ts;
SELECT AddGeometryColumn('riskr', 'loss_curve_data', 'location', 4326, 'POINT',
                         2);
ALTER TABLE riskr.loss_curve_data ALTER COLUMN location SET NOT NULL;


-- Aggregate loss curve data.  Holds the probability of exceedence of certain
-- levels of losses for the whole exposure model.
CREATE TABLE riskr.aggregate_loss_curve_data (
    id SERIAL PRIMARY KEY,
    loss_curve_id INTEGER NOT NULL,

    losses float[] NOT NULL CONSTRAINT non_negative_losses
        CHECK (0 <= ALL(losses)),
    -- Probabilities of exceedence
    poes float[] NOT NULL
) TABLESPACE riskr_ts;


-- Collapse map data.
CREATE TABLE riskr.collapse_map (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    exposure_model_id INTEGER NOT NULL -- FK to exposure_model.id
) TABLESPACE riskr_ts;

CREATE TABLE riskr.collapse_map_data (
    id SERIAL PRIMARY KEY,
    collapse_map_id INTEGER NOT NULL, -- FK to collapse_map.id
    asset_ref VARCHAR NOT NULL,
    value float NOT NULL,
    std_dev float NOT NULL
) TABLESPACE riskr_ts;
SELECT AddGeometryColumn('riskr', 'collapse_map_data', 'location', 4326, 'POINT', 2);
ALTER TABLE riskr.collapse_map_data ALTER COLUMN location SET NOT NULL;


-- Benefit-cost ratio distribution
CREATE TABLE riskr.bcr_distribution (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    exposure_model_id INTEGER NOT NULL -- FK to exposure_model.id
) TABLESPACE riskr_ts;

CREATE TABLE riskr.bcr_distribution_data (
    id SERIAL PRIMARY KEY,
    bcr_distribution_id INTEGER NOT NULL, -- FK to bcr_distribution.id
    asset_ref VARCHAR NOT NULL,
    bcr float NOT NULL CONSTRAINT bcr_value
        CHECK (bcr >= 0.0)
) TABLESPACE riskr_ts;
SELECT AddGeometryColumn('riskr', 'bcr_distribution_data', 'location', 4326, 'POINT', 2);
ALTER TABLE riskr.bcr_distribution_data ALTER COLUMN location SET NOT NULL;


-- Exposure model
CREATE TABLE oqmif.exposure_model (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    description VARCHAR,
    -- e.g. "buildings", "bridges" etc.
    category VARCHAR NOT NULL,
    -- e.g. "EUR", "count", "density" etc.
    unit VARCHAR NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE oqmif_ts;


-- Per-asset exposure data
CREATE TABLE oqmif.exposure_data (
    id SERIAL PRIMARY KEY,
    exposure_model_id INTEGER NOT NULL,
    -- The asset reference is unique within an exposure model.
    asset_ref VARCHAR NOT NULL,
    value float NOT NULL,
    -- Vulnerability function reference
    vf_ref VARCHAR NOT NULL,
    structure_type VARCHAR,
    retrofitting_cost float,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL,
    UNIQUE (exposure_model_id, asset_ref)
) TABLESPACE oqmif_ts;
SELECT AddGeometryColumn('oqmif', 'exposure_data', 'site', 4326, 'POINT', 2);
ALTER TABLE oqmif.exposure_data ALTER COLUMN site SET NOT NULL;


-- Vulnerability model
CREATE TABLE riski.vulnerability_model (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    description VARCHAR,
    imt VARCHAR NOT NULL CONSTRAINT imt_value
        CHECK(imt IN ('pga', 'sa', 'pgv', 'pgd')),
    imls float[] NOT NULL,
    -- e.g. "buildings", "bridges" etc.
    category VARCHAR NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE riski_ts;


-- Vulnerability function
CREATE TABLE riski.vulnerability_function (
    id SERIAL PRIMARY KEY,
    vulnerability_model_id INTEGER NOT NULL,
    -- The vulnerability function reference is unique within an vulnerability
    -- model.
    vf_ref VARCHAR NOT NULL,
    -- Please note: there must be one loss ratio and coefficient of variation
    -- per IML value defined in the referenced vulnerability model.
    loss_ratios float[] NOT NULL CONSTRAINT loss_ratio_values
        CHECK (0.0 <= ALL(loss_ratios) AND 1.0 >= ALL(loss_ratios)),
    -- Coefficients of variation
    covs float[] NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL,
    UNIQUE (vulnerability_model_id, vf_ref)
) TABLESPACE riski_ts;


------------------------------------------------------------------------
-- Constraints (foreign keys etc.) go here
------------------------------------------------------------------------
ALTER TABLE admin.oq_user ADD CONSTRAINT admin_oq_user_organization_fk
FOREIGN KEY (organization_id) REFERENCES admin.organization(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.rupture ADD CONSTRAINT hzrdi_rupture_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.source ADD CONSTRAINT hzrdi_source_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.simple_fault ADD CONSTRAINT hzrdi_simple_fault_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.complex_fault ADD CONSTRAINT hzrdi_complex_fault_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.fault_edge ADD CONSTRAINT hzrdi_fault_edge_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.mfd_evd ADD CONSTRAINT hzrdi_mfd_evd_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.mfd_tgr ADD CONSTRAINT hzrdi_mfd_tgr_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.r_depth_distr ADD CONSTRAINT hzrdi_r_depth_distr_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.focal_mechanism ADD CONSTRAINT hzrdi_focal_mechanism_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.r_rate_mdl ADD CONSTRAINT hzrdi_r_rate_mdl_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.complex_fault ADD CONSTRAINT hzrdi_complex_fault_fault_edge_fk
FOREIGN KEY (fault_edge_id) REFERENCES hzrdi.fault_edge(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.r_rate_mdl ADD CONSTRAINT hzrdi_r_rate_mdl_mfd_tgr_fk
FOREIGN KEY (mfd_tgr_id) REFERENCES hzrdi.mfd_tgr(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.r_rate_mdl ADD CONSTRAINT hzrdi_r_rate_mdl_mfd_evd_fk
FOREIGN KEY (mfd_evd_id) REFERENCES hzrdi.mfd_evd(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.r_rate_mdl ADD CONSTRAINT hzrdi_r_rate_mdl_focal_mechanism_fk
FOREIGN KEY (focal_mechanism_id) REFERENCES hzrdi.focal_mechanism(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.r_rate_mdl ADD CONSTRAINT hzrdi_r_rate_mdl_source_fk
FOREIGN KEY (source_id) REFERENCES hzrdi.source(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.simple_fault ADD CONSTRAINT hzrdi_simple_fault_mfd_tgr_fk
FOREIGN KEY (mfd_tgr_id) REFERENCES hzrdi.mfd_tgr(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.simple_fault ADD CONSTRAINT hzrdi_simple_fault_mfd_evd_fk
FOREIGN KEY (mfd_evd_id) REFERENCES hzrdi.mfd_evd(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.complex_fault ADD CONSTRAINT hzrdi_complex_fault_mfd_tgr_fk
FOREIGN KEY (mfd_tgr_id) REFERENCES hzrdi.mfd_tgr(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.complex_fault ADD CONSTRAINT hzrdi_complex_fault_mfd_evd_fk
FOREIGN KEY (mfd_evd_id) REFERENCES hzrdi.mfd_evd(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.source ADD CONSTRAINT hzrdi_source_simple_fault_fk
FOREIGN KEY (simple_fault_id) REFERENCES hzrdi.simple_fault(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.source ADD CONSTRAINT hzrdi_source_complex_fault_fk
FOREIGN KEY (complex_fault_id) REFERENCES hzrdi.complex_fault(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.source ADD CONSTRAINT hzrdi_source_r_depth_distr_fk
FOREIGN KEY (r_depth_distr_id) REFERENCES hzrdi.r_depth_distr(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.source ADD CONSTRAINT hzrdi_source_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.rupture ADD CONSTRAINT hzrdi_rupture_simple_fault_fk
FOREIGN KEY (simple_fault_id) REFERENCES hzrdi.simple_fault(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.rupture ADD CONSTRAINT hzrdi_rupture_complex_fault_fk
FOREIGN KEY (complex_fault_id) REFERENCES hzrdi.complex_fault(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.rupture ADD CONSTRAINT hzrdi_rupture_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE RESTRICT;

CREATE TRIGGER hzrdi_rupture_before_insert_update_trig
BEFORE INSERT OR UPDATE ON hzrdi.rupture
FOR EACH ROW EXECUTE PROCEDURE check_rupture_sources();

CREATE TRIGGER hzrdi_source_before_insert_update_trig
BEFORE INSERT OR UPDATE ON hzrdi.source
FOR EACH ROW EXECUTE PROCEDURE check_source_sources();

CREATE TRIGGER hzrdi_r_rate_mdl_before_insert_update_trig
BEFORE INSERT OR UPDATE ON hzrdi.r_rate_mdl
FOR EACH ROW EXECUTE PROCEDURE check_only_one_mfd_set();

CREATE TRIGGER hzrdi_simple_fault_before_insert_update_trig
BEFORE INSERT OR UPDATE ON hzrdi.simple_fault
FOR EACH ROW EXECUTE PROCEDURE check_only_one_mfd_set();

CREATE TRIGGER hzrdi_complex_fault_before_insert_update_trig
BEFORE INSERT OR UPDATE ON hzrdi.complex_fault
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

ALTER TABLE uiapi.job_stats ADD CONSTRAINT  uiapi_job_stats_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

ALTER TABLE uiapi.upload ADD CONSTRAINT uiapi_upload_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.oq_params ADD CONSTRAINT uiapi_oq_params_input_set_fk
FOREIGN KEY (input_set_id) REFERENCES uiapi.input_set(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.input ADD CONSTRAINT uiapi_input_input_set_fk
FOREIGN KEY (input_set_id) REFERENCES uiapi.input_set(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.input_set ADD CONSTRAINT uiapi_input_set_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.input_set ADD CONSTRAINT uiapi_input_set_upload_fk
FOREIGN KEY (upload_id) REFERENCES uiapi.upload(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.output ADD CONSTRAINT uiapi_output_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.output ADD CONSTRAINT uiapi_output_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.error_msg ADD CONSTRAINT uiapi_error_msg_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

ALTER TABLE oqmif.exposure_model ADD CONSTRAINT oqmif_exposure_model_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE riski.vulnerability_model ADD CONSTRAINT
riski_vulnerability_model_owner_fk FOREIGN KEY (owner_id) REFERENCES
admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE hzrdr.hazard_map
ADD CONSTRAINT hzrdr_hazard_map_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE hzrdr.hazard_map_data
ADD CONSTRAINT hzrdr_hazard_map_data_hazard_map_fk
FOREIGN KEY (hazard_map_id) REFERENCES hzrdr.hazard_map(id) ON DELETE CASCADE;

ALTER TABLE hzrdr.hazard_curve
ADD CONSTRAINT hzrdr_hazard_curve_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE hzrdr.hazard_curve_data
ADD CONSTRAINT hzrdr_hazard_curve_data_hazard_curve_fk
FOREIGN KEY (hazard_curve_id) REFERENCES hzrdr.hazard_curve(id) ON DELETE CASCADE;

ALTER TABLE hzrdr.gmf_data
ADD CONSTRAINT hzrdr_gmf_data_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.loss_map
ADD CONSTRAINT riskr_loss_map_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.loss_curve
ADD CONSTRAINT riskr_loss_curve_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.collapse_map
ADD CONSTRAINT riskr_collapse_map_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.collapse_map
ADD CONSTRAINT riskr_collapse_map_exposure_model_fk
FOREIGN KEY (exposure_model_id) REFERENCES oqmif.exposure_model(id) ON DELETE RESTRICT;

ALTER TABLE riskr.bcr_distribution
ADD CONSTRAINT riskr_bcr_distribution_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.bcr_distribution
ADD CONSTRAINT riskr_bcr_distribution_exposure_model_fk
FOREIGN KEY (exposure_model_id) REFERENCES oqmif.exposure_model(id) ON DELETE RESTRICT;

ALTER TABLE riskr.loss_curve_data
ADD CONSTRAINT riskr_loss_curve_data_loss_curve_fk
FOREIGN KEY (loss_curve_id) REFERENCES riskr.loss_curve(id) ON DELETE CASCADE;

ALTER TABLE riskr.aggregate_loss_curve_data
ADD CONSTRAINT riskr_aggregate_loss_curve_data_loss_curve_fk
FOREIGN KEY (loss_curve_id) REFERENCES riskr.loss_curve(id) ON DELETE CASCADE;

ALTER TABLE riskr.loss_map_data
ADD CONSTRAINT riskr_loss_map_data_loss_map_fk
FOREIGN KEY (loss_map_id) REFERENCES riskr.loss_map(id) ON DELETE CASCADE;

ALTER TABLE riskr.collapse_map_data
ADD CONSTRAINT riskr_collapse_map_data_collapse_map_fk
FOREIGN KEY (collapse_map_id) REFERENCES riskr.collapse_map(id) ON DELETE CASCADE;

ALTER TABLE riskr.bcr_distribution_data
ADD CONSTRAINT riskr_bcr_distribution_data_bcr_distribution_fk
FOREIGN KEY (bcr_distribution_id) REFERENCES riskr.bcr_distribution(id) ON DELETE CASCADE;

ALTER TABLE oqmif.exposure_data ADD CONSTRAINT
oqmif_exposure_data_exposure_model_fk FOREIGN KEY (exposure_model_id)
REFERENCES oqmif.exposure_model(id) ON DELETE CASCADE;

ALTER TABLE riski.vulnerability_function ADD CONSTRAINT
riski_vulnerability_function_vulnerability_model_fk FOREIGN KEY
(vulnerability_model_id) REFERENCES riski.vulnerability_model(id) ON DELETE
CASCADE;

CREATE TRIGGER eqcat_magnitude_before_insert_update_trig
BEFORE INSERT OR UPDATE ON eqcat.magnitude
FOR EACH ROW EXECUTE PROCEDURE check_magnitude_data();

CREATE TRIGGER admin_organization_refresh_last_update_trig BEFORE UPDATE ON admin.organization FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER admin_oq_user_refresh_last_update_trig BEFORE UPDATE ON admin.oq_user FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER eqcat_catalog_refresh_last_update_trig BEFORE UPDATE ON eqcat.catalog FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER eqcat_surface_refresh_last_update_trig BEFORE UPDATE ON eqcat.surface FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER hzrdi_fault_edge_refresh_last_update_trig BEFORE UPDATE ON hzrdi.fault_edge FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER hzrdi_mfd_evd_refresh_last_update_trig BEFORE UPDATE ON hzrdi.mfd_evd FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER hzrdi_mfd_tgr_refresh_last_update_trig BEFORE UPDATE ON hzrdi.mfd_tgr FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER hzrdi_r_depth_distr_refresh_last_update_trig BEFORE UPDATE ON hzrdi.r_depth_distr FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER hzrdi_focal_mechanism_refresh_last_update_trig BEFORE UPDATE ON hzrdi.focal_mechanism FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER oqmif_exposure_model_refresh_last_update_trig BEFORE UPDATE ON oqmif.exposure_model FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER oqmif_exposure_data_refresh_last_update_trig BEFORE UPDATE ON oqmif.exposure_data FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER riski_vulnerability_function_refresh_last_update_trig BEFORE UPDATE ON riski.vulnerability_function FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER riski_vulnerability_model_refresh_last_update_trig BEFORE UPDATE ON riski.vulnerability_model FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

CREATE TRIGGER uiapi_input_set_refresh_last_update_trig BEFORE UPDATE ON uiapi.input_set FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();
