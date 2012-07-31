/*
  OpenQuake database schema definitions.

    Copyright (c) 2010-2012, GEM Foundation.

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
CREATE SCHEMA htemp;



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


-- Site-specific parameters for hazard calculations.
CREATE TABLE hzrdi.site_model (
    id SERIAL PRIMARY KEY,
    input_id INTEGER NOT NULL,
    -- Average shear wave velocity for top 30 m. Units m/s.
    vs30 float NOT NULL CONSTRAINT site_model_vs30
        CHECK(vs30 > 0.0),
    -- 'measured' or 'inferred'. Identifies if vs30 value has been measured or inferred.
    vs30_type VARCHAR NOT NULL CONSTRAINT site_model_vs30_type
        CHECK(vs30_type in ('measured', 'inferred')),
    -- Depth to shear wave velocity of 1.0 km/s. Units m.
    z1pt0 float NOT NULL CONSTRAINT site_model_z1pt0
        CHECK(z1pt0 > 0.0),
    -- Depth to shear wave velocity of 2.5 km/s. Units km.
    z2pt5 float NOT NULL CONSTRAINT site_model_z2pt5
        CHECK(z2pt5 > 0.0)
) TABLESPACE hzrdi_ts;
SELECT AddGeometryColumn('hzrdi', 'site_model', 'location', 4326, 'POINT', 2);


-- Parsed sources
CREATE TABLE hzrdi.parsed_source (
    id SERIAL PRIMARY KEY,
    input_id INTEGER NOT NULL,
    source_type VARCHAR NOT NULL
        CONSTRAINT enforce_source_type CHECK
        (source_type IN ('area', 'point', 'complex', 'simple')),
    nrml BYTEA NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE hzrdi_ts;
-- The surface projection (2D) of the "rupture enclosing" polygon for each source.
-- This is relevant to all source types, including point sources.
-- When considering a parsed_source record given a minimum integration distance,
-- use this polygon in distance calculations.
SELECT AddGeometryColumn('hzrdi', 'parsed_source', 'polygon', 4326, 'POLYGON', 2);
ALTER TABLE hzrdi.parsed_source ALTER COLUMN polygon SET NOT NULL;


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
    model_content_id INTEGER,  -- TODO(larsbutler), May 11th 2012: Eventually make this is a required FK (NOT NULL).
    -- Optional name for the input.
    name VARCHAR,
    -- The full path of the input file on the server
    path VARCHAR NOT NULL,
    digest VARCHAR(32) NOT NULL,
    -- Input file type, one of:
    --      source model file (source)
    --      source logic tree (lt_source)
    --      GSIM logic tree (lt_gsim)
    --      exposure file (exposure)
    --      vulnerability file (vulnerability)
    --      rupture file (rupture)
    input_type VARCHAR NOT NULL CONSTRAINT input_type_value
        CHECK(input_type IN ('unknown', 'source', 'lt_source', 'lt_gsim',
                             'exposure', 'fragility', 'rupture',
                             'vulnerability', 'vulnerability_retrofitted',
                             'site_model')),
    -- Number of bytes in file
    size INTEGER NOT NULL DEFAULT 0,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;


CREATE TABLE uiapi.model_content (
    id SERIAL PRIMARY KEY,
    -- contains the raw text of an input file
    raw_content TEXT NOT NULL,
    content_type VARCHAR NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;


-- An OpenQuake engine run started by the user
CREATE TABLE uiapi.oq_job (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    hazard_calculation_id INTEGER,  -- FK to uiapi.hazard_calculation
    -- One of: pre_execution, executing, post_execution, post_processing, complete
    status VARCHAR NOT NULL DEFAULT 'pre_executing' CONSTRAINT job_status_value
        CHECK(status IN ('pre_executing', 'executing', 'post_executing', 'post_processing', 'complete')),
    oq_version VARCHAR,
    nhlib_version VARCHAR,
    nrml_version VARCHAR,
    is_running BOOLEAN NOT NULL DEFAULT FALSE,
    duration INTEGER NOT NULL DEFAULT 0,
    job_pid INTEGER NOT NULL DEFAULT 0,
    supervisor_pid INTEGER NOT NULL DEFAULT 0,
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
    num_sites INTEGER NOT NULL,
    -- The number of logic tree samples (for hazard jobs of all types except scenario)
    realizations INTEGER
) TABLESPACE uiapi_ts;


CREATE TABLE uiapi.hazard_calculation (
    -- TODO(larsbutler): At the moment, this model only contains Classical hazard parameters.
    -- We'll need to update fields and constraints as we add the other calculation modes.
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- Contains the absolute path to the directory containing the job config file
    base_path VARCHAR NOT NULL,
    force_inputs BOOLEAN NOT NULL,
    -- general parameters:
    -- (see also `region` and `sites` geometries defined below)
    description VARCHAR NOT NULL DEFAULT '',
    calculation_mode VARCHAR NOT NULL CONSTRAINT haz_calc_mode
        CHECK(calculation_mode IN ('classical', 'event_based')),
    region_grid_spacing float,
    -- logic tree parameters:
    random_seed INTEGER,
    number_of_logic_tree_samples INTEGER,
    -- ERF parameters:
    rupture_mesh_spacing float NOT NULL,
    width_of_mfd_bin float NOT NULL,
    area_source_discretization float NOT NULL,
    -- site parameters:
    reference_vs30_value float,
    reference_vs30_type VARCHAR CONSTRAINT vs30_type
        CHECK(((reference_vs30_type IS NULL)
               OR
               (reference_vs30_type IN ('measured', 'inferred')))),
    reference_depth_to_2pt5km_per_sec float,
    reference_depth_to_1pt0km_per_sec float,
    -- calculation parameters:
    investigation_time float NOT NULL,
    intensity_measure_types_and_levels bytea NOT NULL,  -- stored as a pickled Python `dict`
    truncation_level float NOT NULL,
    maximum_distance float NOT NULL,
    -- event-based calculator parameters:
    intensity_measure_types VARCHAR[],
    ses_per_sample INTEGER,
    ground_motion_correlation_model VARCHAR,
    ground_motion_correlation_params bytea, -- stored as a pickled Python `dict`
    -- output/post-processing parameters:
    -- classical:
    mean_hazard_curves boolean DEFAULT false,
    quantile_hazard_curves float[],
    poes_hazard_maps float[],
    -- event-based:
    complete_logic_tree_ses BOOLEAN,
    ground_motion_fields BOOLEAN
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'hazard_calculation', 'region', 4326, 'POLYGON', 2);
SELECT AddGeometryColumn('uiapi', 'hazard_calculation', 'sites', 4326, 'MULTIPOINT', 2);


CREATE TABLE uiapi.input2hcalc (
    id SERIAL PRIMARY KEY,
    input_id INTEGER NOT NULL,
    hazard_calculation_id INTEGER NOT NULL
) TABLESPACE uiapi_ts;


-- The parameters needed for an OpenQuake engine run
CREATE TABLE uiapi.oq_job_profile (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    force_inputs boolean NOT NULL DEFAULT false,
    description VARCHAR NOT NULL DEFAULT '',
    -- One of:
    --      classical (Classical PSHA)
    --      event_based (Probabilistic event based)
    --      scenario (Scenario)
    --      scenario_damage (Scenario Damage Assessment)
    --      disaggregation (Hazard only)
    --      uhs (Uniform Hazard Spectra; Hazard only)
    --      classical_bcr (Benefit-cost ratio calc based on Classical PSHA)
    --      event_based_bcr (BCR calc based on Probabilistic event-based)
    -- Note: 'classical' and 'event_based' are both probabilistic methods
    calc_mode VARCHAR NOT NULL CONSTRAINT calc_mode_value
        CHECK(calc_mode IN ('classical', 'event_based', 'scenario',
                            'disaggregation', 'uhs', 'scenario_damage',
                            'classical_bcr', 'event_based_bcr')),
    -- Job type: hazard and/or risk.
    job_type VARCHAR[] CONSTRAINT job_type_value
        CHECK(((job_type IS NOT NULL)
           -- The array_length() function is supposed to return an int,
           -- but if you pass it zero-length array, is returns NULL instead of 0.
           AND (array_length(job_type, 1) IS NOT NULL)
            AND (job_type <@ ARRAY['hazard', 'risk']::VARCHAR[]))),
    region_grid_spacing float,
    min_magnitude float CONSTRAINT min_magnitude_set
        CHECK(
            ((calc_mode IN ('scenario', 'scenario_damage')) AND (min_magnitude IS NULL))
            OR ((calc_mode NOT IN ('scenario', 'scenario_damage')) AND (min_magnitude IS NOT NULL))),
    investigation_time float CONSTRAINT investigation_time_set
        CHECK(
            ((calc_mode IN ('scenario', 'scenario_damage')) AND (investigation_time IS NULL))
            OR ((calc_mode NOT IN ('scenario', 'scenario_damage')) AND (investigation_time IS NOT NULL))),
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
    --      Arias Intensity (ia)
    --      relative significant duration (rsd)
    --      Modified Mercalli Intensity
    -- For UHS calculations, IMT should always be 'sa'.
    imt VARCHAR,
    period float,
    damping float CONSTRAINT damping_is_set
        CHECK(((imt = 'sa') AND (damping IS NOT NULL))
              OR ((imt != 'sa') AND (damping IS NULL))),
    truncation_type VARCHAR NOT NULL CONSTRAINT truncation_type_value
        CHECK(truncation_type IN ('none', 'onesided', 'twosided')),
    truncation_level float NOT NULL DEFAULT 3.0,
    -- Intensity measure levels
    imls float[] CONSTRAINT imls_are_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage')) AND (imls IS NOT NULL))
            OR ((calc_mode IN ('scenario', 'scenario_damage')) AND (imls IS NULL))),
    -- Probabilities of exceedence
    poes float[] CONSTRAINT poes_are_set
        CHECK(
            ((calc_mode IN ('classical', 'disaggregation', 'uhs')) AND (poes IS NOT NULL))
            OR ((calc_mode IN ('event_based', 'scenario', 'scenario_damage',
                              'classical_bcr', 'event_based_bcr')) AND (poes IS NULL))),
    -- Number of logic tree samples
    realizations integer CONSTRAINT realizations_is_set
        CHECK(
            ((calc_mode IN ('scenario', 'scenario_damage')) AND (realizations IS NULL))
            OR ((calc_mode NOT IN ('scenario', 'scenario_damage')) AND (realizations IS NOT NULL))),
    -- Number of seismicity histories
    histories integer CONSTRAINT histories_is_set
        CHECK(
            ((calc_mode IN ('event_based', 'event_based_bcr') AND (histories IS NOT NULL))
            OR (calc_mode NOT IN ('event_based', 'event_based_bcr')) AND (histories IS NULL))),
    -- ground motion correlation flag
    gm_correlated boolean CONSTRAINT gm_correlated_is_set
        CHECK(
            ((calc_mode IN ('classical', 'disaggregation', 'uhs',
                           'classical_bcr', 'event_based_bcr')) AND (gm_correlated IS NULL))
            OR ((calc_mode IN ('event_based', 'scenario', 'scenario_damage', 'event_based_bcr')) AND (gm_correlated IS NOT NULL))),
    gmf_calculation_number integer CONSTRAINT gmf_calculation_number_is_set
        CHECK(
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (gmf_calculation_number IS NOT NULL)
             AND (realizations > 0))
            OR
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (gmf_calculation_number IS NULL))),
    rupture_surface_discretization float
        CONSTRAINT rupture_surface_discretization_is_set
        CHECK(
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (rupture_surface_discretization IS NOT NULL)
             AND (rupture_surface_discretization > 0))
            OR
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (rupture_surface_discretization IS NULL))),
    asset_correlation VARCHAR,
    area_source_discretization float
        CONSTRAINT area_source_discretization_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage')) AND (area_source_discretization IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage')) AND (area_source_discretization IS NULL))),
    area_source_magnitude_scaling_relationship VARCHAR
        CONSTRAINT area_source_magnitude_scaling_relationship_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (area_source_magnitude_scaling_relationship IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (area_source_magnitude_scaling_relationship IS NULL))),
    asset_life_expectancy float
        CONSTRAINT asset_life_expectancy_is_set
        CHECK (
            ((calc_mode IN ('classical_bcr', 'event_based_bcr'))
             AND asset_life_expectancy IS NOT NULL)
            OR
            ((calc_mode NOT IN ('classical_bcr', 'event_based_bcr'))
             AND asset_life_expectancy IS NULL)),
    compute_mean_hazard_curve boolean
        CONSTRAINT compute_mean_hazard_curve_is_set
        CHECK(
            ((calc_mode IN ('classical', 'classical_bcr'))
            AND
            (
                -- If the job is hazard+risk and classical,
                -- make sure compute_mean_hazard_curve is TRUE.
                ((ARRAY['hazard', 'risk']::VARCHAR[] <@ job_type) AND (compute_mean_hazard_curve = TRUE))
                OR
                -- If the job is just classical (and not hazard+risk),
                -- just make sure compute_mean_hazard_curve is not null.
                ((NOT ARRAY['hazard', 'risk']::VARCHAR[] <@ job_type) AND (compute_mean_hazard_curve IS NOT NULL))
            ))
            OR
            ((calc_mode NOT IN ('classical', 'classical_bcr'))
             AND (compute_mean_hazard_curve IS NULL))),
    conditional_loss_poe float[],
    fault_magnitude_scaling_relationship VARCHAR
        CONSTRAINT fault_magnitude_scaling_relationship_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (fault_magnitude_scaling_relationship IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (fault_magnitude_scaling_relationship IS NULL))),
    fault_magnitude_scaling_sigma float
        CONSTRAINT fault_magnitude_scaling_sigma_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (fault_magnitude_scaling_sigma IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (fault_magnitude_scaling_sigma IS NULL))),
    fault_rupture_offset float
        CONSTRAINT fault_rupture_offset_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (fault_rupture_offset IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (fault_rupture_offset IS NULL))),
    fault_surface_discretization float
        CONSTRAINT fault_surface_discretization_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (fault_surface_discretization IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (fault_surface_discretization IS NULL))),
    gmf_random_seed integer
        CONSTRAINT gmf_random_seed_is_set
        CHECK(
            (calc_mode IN ('scenario', 'scenario_damage', 'event_based')
             AND (gmf_random_seed IS NOT NULL))
            OR
            ((calc_mode NOT IN ('scenario', 'scenario_damage', 'event_based'))
             AND (gmf_random_seed IS NULL))),
    gmpe_lt_random_seed integer
        CONSTRAINT gmpe_lt_random_seed_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (gmpe_lt_random_seed IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (gmpe_lt_random_seed IS NULL))),
    gmpe_model_name VARCHAR,
    grid_source_magnitude_scaling_relationship VARCHAR,
    include_area_sources boolean
        CONSTRAINT include_area_sources_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (include_area_sources IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (include_area_sources IS NULL))),
    include_fault_source boolean
        CONSTRAINT include_fault_source_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (include_fault_source IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (include_fault_source IS NULL))),
    include_grid_sources boolean
        CONSTRAINT include_grid_sources_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (include_grid_sources IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (include_grid_sources IS NULL))),
    include_subduction_fault_source boolean
        CONSTRAINT include_subduction_fault_source_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (include_subduction_fault_source IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (include_subduction_fault_source IS NULL))),
    interest_rate float
        CONSTRAINT interest_rate_is_set
        CHECK (
            ((calc_mode IN ('classical_bcr', 'event_based_bcr'))
             AND interest_rate IS NOT NULL)
            OR
            ((calc_mode NOT IN ('classical_bcr', 'event_based_bcr'))
             AND interest_rate IS NULL)),
    -- Loss Ratio Exceedence Matrix steps per interval
    -- Only used for Classical/Classical BCR Risk calculations.
    lrem_steps_per_interval integer
        CONSTRAINT lrem_steps_is_set
        CHECK (
            (calc_mode in ('classical', 'classical_bcr'))
            AND
            (
                -- If this is a Classical or Classical BCR Risk calculation,
                -- lrem_steps_per_interval needs to set.
                ((ARRAY['risk']::VARCHAR[] <@ job_type)
                 AND (lrem_steps_per_interval IS NOT NULL))
                OR
                -- If it's not a Risk calculation, it should be NULL.
                ((NOT ARRAY['risk']::VARCHAR[] <@ job_type)
                 AND (lrem_steps_per_interval IS NULL))
            )
            OR
            (
                (calc_mode NOT IN ('classical', 'classical_bcr'))
                AND (lrem_steps_per_interval IS NULL)
            )),
    loss_curves_output_prefix VARCHAR,
    -- Number of bins in the compute loss histogram.
    -- For Event-Based Risk calculations only.
    loss_histogram_bins INTEGER
        CONSTRAINT loss_histogram_bins_is_set
        CHECK (
            (calc_mode in ('event_based', 'event_based_bcr'))
            AND
            (
                ((ARRAY['risk']::VARCHAR[] <@ job_type)
                 AND (loss_histogram_bins is NOT NULL)
                 AND (loss_histogram_bins >= 1))
                OR
                ((NOT ARRAY['risk']::VARCHAR[] <@ job_type)
                 AND (loss_histogram_bins IS NULL))
            )
            OR
            (
                (calc_mode NOT IN ('event_based', 'event_based_bcr')
                 AND (loss_histogram_bins IS NULL))
            )),
    maximum_distance float
        CONSTRAINT maximum_distance_is_set
        CHECK(
            ((calc_mode IN ('classical', 'disaggregation', 'uhs',
                           'classical_bcr', 'event_based_bcr'))
             AND (maximum_distance IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage', 'event_based'))
             AND (maximum_distance IS NULL))),
    quantile_levels float[]
        CONSTRAINT quantile_levels_is_set
        CHECK(
            ((calc_mode = 'classical')
             AND (quantile_levels IS NOT NULL))
            OR
            ((calc_mode != 'classical')
             AND (quantile_levels IS NULL))),
    rupture_aspect_ratio float
        CONSTRAINT rupture_aspect_ratio_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (rupture_aspect_ratio IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (rupture_aspect_ratio IS NULL))),
    -- Rupture floating type, one of:
    --     Only along strike ( rupture full DDW) (alongstrike)
    --     Along strike and down dip (downdip)
    --     Along strike & centered down dip (centereddowndip)
    rupture_floating_type VARCHAR
        CONSTRAINT rupture_floating_type_is_set
        CHECK(
            ((calc_mode IN ('classical', 'event_based', 'disaggregation', 'uhs',
                           'classical_bcr', 'event_based_bcr'))
             AND (rupture_floating_type IN ('alongstrike', 'downdip', 'centereddowndip')))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
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
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (source_model_lt_random_seed IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
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
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (standard_deviation_type IN ('total', 'interevent', 'intraevent', 'zero', 'total_mag_dependent', 'total_pga_dependent', 'intraevent_mag_dependent')))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (standard_deviation_type IS NULL))),
    subduction_fault_magnitude_scaling_relationship VARCHAR
        CONSTRAINT subduction_fault_magnitude_scaling_relationship_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (subduction_fault_magnitude_scaling_relationship IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (subduction_fault_magnitude_scaling_relationship IS NULL))),
    subduction_fault_magnitude_scaling_sigma float
        CONSTRAINT subduction_fault_magnitude_scaling_sigma_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (subduction_fault_magnitude_scaling_sigma IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (subduction_fault_magnitude_scaling_sigma IS NULL))),
    subduction_fault_rupture_offset float
        CONSTRAINT subduction_fault_rupture_offset_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (subduction_fault_rupture_offset IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (subduction_fault_rupture_offset IS NULL))),
    subduction_fault_surface_discretization float
        CONSTRAINT subduction_fault_surface_discretization_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (subduction_fault_surface_discretization IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (subduction_fault_surface_discretization IS NULL))),
    subduction_rupture_aspect_ratio float
        CONSTRAINT subduction_rupture_aspect_ratio_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (subduction_rupture_aspect_ratio IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (subduction_rupture_aspect_ratio IS NULL))),
    -- Rupture floating type, one of:
    --     Only along strike ( rupture full DDW) (alongstrike)
    --     Along strike and down dip (downdip)
    --     Along strike & centered down dip (centereddowndip)
    subduction_rupture_floating_type VARCHAR
        CONSTRAINT subduction_rupture_floating_type_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (subduction_rupture_floating_type IN ('alongstrike', 'downdip', 'centereddowndip')))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (subduction_rupture_floating_type IS NULL))),
    -- Source as, one of:
    --     Point Sources (pointsources)
    --     Line Sources (random or given strike) (linesources)
    --     Cross Hair Line Sources (crosshairsources)
    --     16 Spoked Line Sources (16spokedsources)
    treat_area_source_as VARCHAR
        CONSTRAINT treat_area_source_as_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (treat_area_source_as IN ('pointsources', 'linesources', 'crosshairsources', '16spokedsources')))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (treat_area_source_as IS NULL))),
    treat_grid_source_as VARCHAR
        CONSTRAINT treat_grid_source_as_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (treat_grid_source_as IN ('pointsources', 'linesources', 'crosshairsources', '16spokedsources')))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (treat_grid_source_as IS NULL))),
    width_of_mfd_bin float
        CONSTRAINT width_of_mfd_bin_is_set
        CHECK(
            ((calc_mode NOT IN ('scenario', 'scenario_damage'))
             AND (width_of_mfd_bin IS NOT NULL))
            OR
            ((calc_mode IN ('scenario', 'scenario_damage'))
             AND (width_of_mfd_bin IS NULL))),
    lat_bin_limits float[]
        CONSTRAINT lat_bin_limits_valid
        CHECK(
            (((calc_mode = 'disaggregation')
            AND (lat_bin_limits IS NOT NULL)
            AND (-90 <= all(lat_bin_limits))
            AND (90 >= all(lat_bin_limits))
            OR
            ((calc_mode != 'disaggregation')
            AND (lat_bin_limits IS NULL))))),
    lon_bin_limits float[]
        CONSTRAINT lon_bin_limits_valid
        CHECK(
            (((calc_mode = 'disaggregation')
            AND (lon_bin_limits IS NOT NULL)
            AND (-180 <= all(lon_bin_limits))
            AND (180 >= all(lon_bin_limits))
            OR
            ((calc_mode != 'disaggregation')
            AND (lon_bin_limits IS NULL))))),
    mag_bin_limits float[]
        CONSTRAINT mag_bin_limits_is_set
        CHECK(
            ((calc_mode = 'disaggregation')
            AND (mag_bin_limits IS NOT NULL))
            OR
            ((calc_mode != 'disaggregation')
            AND (mag_bin_limits IS NULL))),
    epsilon_bin_limits float[]
        CONSTRAINT epsilon_bin_limits_is_set
        CHECK(
            ((calc_mode = 'disaggregation')
            AND (epsilon_bin_limits IS NOT NULL))
            OR
            ((calc_mode != 'disaggregation')
            AND (epsilon_bin_limits IS NULL))),
    distance_bin_limits float[]
        CONSTRAINT distance_bin_limits_is_set
        CHECK(
            ((calc_mode = 'disaggregation')
            AND (distance_bin_limits IS NOT NULL))
            OR
            ((calc_mode != 'disaggregation')
            AND (distance_bin_limits IS NULL))),
    -- For disaggregation results, choose any (at least 1) of the following:
    --      MagPMF (Magnitude Probability Mass Function)
    --      DistPMF (Distance PMF)
    --      TRTPMF (Tectonic Region Type PMF)
    --      MagDistPMF (Magnitude-Distance PMF)
    --      MagDistEpsPMF (Magnitude-Distance-Epsilon PMF)
    --      LatLonPMF (Latitude-Longitude PMF)
    --      LatLonMagPMF (Latitude-Longitude-Magnitude PMF)
    --      LatLonMagEpsPMF (Latitude-Longitude-Magnitude-Epsilon PMF)
    --      MagTRTPMF (Magnitude-Tectonic Region Type PMF)
    --      LatLonTRTPMF (Latitude-Longitude-Tectonic Region Type PMF)
    --      FullDisaggMatrix (The full disaggregation matrix; includes
    --          Lat, Lon, Magnitude, Epsilon, and Tectonic Region Type)
    disagg_results VARCHAR[]
        CONSTRAINT disagg_results_valid
        CHECK(
            (((calc_mode = 'disaggregation')
            AND (disagg_results IS NOT NULL)
            -- array_length() returns NULL instead 0 when the array length is 0;
            -- I have no idea why.
            AND (array_length(disagg_results, 1) IS NOT NULL)
            AND (disagg_results <@ ARRAY['MagPMF', 'DistPMF', 'TRTPMF',
                                         'MagDistPMF', 'MagDistEpsPMF',
                                         'LatLonPMF', 'LatLonMagPMF',
                                         'LatLonMagEpsPMF',
                                         'MagTRTPMF', 'LatLonTRTPMF',
                                         'FullDisaggMatrix']::VARCHAR[]))
            OR
            ((calc_mode != 'disaggregation')
            AND (disagg_results IS NULL)))),
    uhs_periods float[]
        CONSTRAINT uhs_periods_is_set
        CHECK(
            -- If calc mode is UHS, uhs_periods must be not null and contain at least 1 element
            ((calc_mode = 'uhs') AND (uhs_periods IS NOT NULL) AND (array_length(uhs_periods, 1) > 0))
            OR
            ((calc_mode != 'uhs') AND (uhs_periods IS NULL))),
    reference_vs30_value float,
    vs30_type VARCHAR DEFAULT 'measured' CONSTRAINT vs30_type_value
        CHECK(vs30_type IN ('measured', 'inferred')),
    depth_to_1pt_0km_per_sec float DEFAULT 100.0
        CONSTRAINT depth_to_1pt_0km_per_sec_above_zero
        CHECK(depth_to_1pt_0km_per_sec > 0.0),
    reference_depth_to_2pt5km_per_sec_param float,
    -- timestamp
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'oq_job_profile', 'region', 4326, 'POLYGON', 2);
SELECT AddGeometryColumn('uiapi', 'oq_job_profile', 'sites', 4326, 'MULTIPOINT', 2);
-- Params can either contain a site list ('sites') or
-- region + region_grid_spacing, but not both.
ALTER TABLE uiapi.oq_job_profile ADD CONSTRAINT oq_job_profile_geometry CHECK(
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
    -- Output type, one of:
    --      hazard_curve
    --      hazard_map
    --      gmf
    --      ses
    --      loss_curve
    --      loss_map
    --      collapse_map
    --      bcr_distribution
    --      agg_loss_curve
    --      dmg_dist_per_asset
    --      dmg_dist_per_taxonomy
    --      dmg_dist_total
    output_type VARCHAR NOT NULL CONSTRAINT output_type_value
        CHECK(output_type IN ('unknown', 'hazard_curve', 'hazard_map',
            'gmf', 'ses', 'loss_curve', 'loss_map', 'collapse_map',
            'bcr_distribution', 'uh_spectra', 'agg_loss_curve',
            'dmg_dist_per_asset', 'dmg_dist_per_taxonomy', 'dmg_dist_total')),
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


-- Associate inputs and jobs
CREATE TABLE uiapi.input2job (
    id SERIAL PRIMARY KEY,
    input_id INTEGER NOT NULL,
    oq_job_id INTEGER NOT NULL,
    UNIQUE (input_id, oq_job_id)
) TABLESPACE uiapi_ts;


-- Associate an 'lt_source' type input (a logic tree source) with 'source'
-- type inputs (hazard sources referenced by the logic tree source).
-- This is needed for worker-side logic tree processing.
CREATE TABLE uiapi.src2ltsrc (
    id SERIAL PRIMARY KEY,
    -- foreign key to the input of type 'source'
    hzrd_src_id INTEGER NOT NULL,
    -- foreign key to the input of type 'lt_source'
    lt_src_id INTEGER NOT NULL,
    -- Due to input file reuse, the original file name may deviate from
    -- the current. We hence need to capture the latter.
    filename VARCHAR NOT NULL,
    UNIQUE (hzrd_src_id, lt_src_id)
) TABLESPACE uiapi_ts;


-- Associate inputs and uploads
CREATE TABLE uiapi.input2upload (
    id SERIAL PRIMARY KEY,
    input_id INTEGER NOT NULL,
    upload_id INTEGER NOT NULL,
    UNIQUE (input_id, upload_id)
) TABLESPACE uiapi_ts;


-- Associate jobs and their profiles, a job may be associated with one profile
-- only.
CREATE TABLE uiapi.job2profile (
    id SERIAL PRIMARY KEY,
    oq_job_id INTEGER NOT NULL,
    oq_job_profile_id INTEGER NOT NULL,
    UNIQUE (oq_job_id)
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
    lt_realization_id INTEGER,  -- lt_realization FK, only required for non-statistical curves
    investigation_time float NOT NULL,
    imt VARCHAR NOT NULL CONSTRAINT hazard_curve_imt
        CHECK(imt in ('PGA', 'PGV', 'PGD', 'SA', 'IA', 'RSD', 'MMI')),
    imls float[] NOT NULL,
    statistics VARCHAR CONSTRAINT hazard_curve_statistics
        CHECK(statistics IS NULL OR
              statistics IN ('mean', 'quantile')),
    -- Quantile value (only for "quantile" statistics)
    quantile float CONSTRAINT quantile_value
        CHECK(
            ((statistics = 'quantile') AND (quantile IS NOT NULL))
            OR (((statistics != 'quantile') AND (quantile IS NULL)))),
    sa_period float CONSTRAINT hazard_curve_sa_period
        CHECK(
            ((imt = 'SA') AND (sa_period IS NOT NULL))
            OR ((imt != 'SA') AND (sa_period IS NULL))),
    sa_damping float CONSTRAINT hazard_curve_sa_damping
        CHECK(
            ((imt = 'SA') AND (sa_damping IS NOT NULL))
            OR ((imt != 'SA') AND (sa_damping IS NULL)))
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


-- Stochastic Event Set Collection
-- A container for all of the Stochastic Event Sets in a given
-- logic tree realization.
CREATE TABLE hzrdr.ses_collection (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    lt_realization_id INTEGER NOT NULL
) TABLESPACE hzrdr_ts;

-- Stochastic Event Set: A container for 1 or more ruptures associated with a
-- specific investigation time span.
CREATE TABLE hzrdr.ses (
    id SERIAL PRIMARY KEY,
    ses_collection_id INTEGER NOT NULL,
    investigation_time float NOT NULL
) TABLESPACE hzrdr_ts;

-- A rupture as part of a Stochastic Event Set.
-- Ruptures will have different geometrical definitions, depending on whether
-- the event was generated from a point/area source or a simple/complex fault
-- source.
CREATE TABLE hzrdr.ses_rupture (
    id SERIAL PRIMARY KEY,
    ses_id INTEGER NOT NULL,
    magnitude float NOT NULL,
    strike float NOT NULL,
    dip float NOT NULL,
    rake float NOT NULL,
    tectonic_region_type VARCHAR NOT NULL,
    is_from_fault_source BOOLEAN NOT NULL,
    lons BYTEA NOT NULL,
    lats BYTEA NOT NULL,
    depths BYTEA NOT NULL
) TABLESPACE hzrdr_ts;


CREATE TABLE hzrdr.gmf_collection (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,  -- FK to output.id
    lt_realization_id INTEGER NOT NULL -- FK to lt_realization.id
) TABLESPACE hzrdr_ts;

CREATE TABLE hzrdr.gmf_set (
    id SERIAL PRIMARY KEY,
    gmf_collection_id INTEGER NOT NULL,  -- FK to gmf_collection.id
    investigation_time float NOT NULL
) TABLESPACE hzrdr_ts;

CREATE TABLE hzrdr.gmf (
    id SERIAL PRIMARY KEY,
    gmf_set_id INTEGER NOT NULL,  -- FK to gmf_set.id
    imt VARCHAR NOT NULL CONSTRAINT hazard_curve_imt
        CHECK(imt in ('PGA', 'PGV', 'PGD', 'SA', 'IA', 'RSD', 'MMI')),
    sa_period float CONSTRAINT gmf_sa_period
        CHECK(
            ((imt = 'SA') AND (sa_period IS NOT NULL))
            OR ((imt != 'SA') AND (sa_period IS NULL))),
    sa_damping float CONSTRAINT gmf_sa_damping
        CHECK(
            ((imt = 'SA') AND (sa_damping IS NOT NULL))
            OR ((imt != 'SA') AND (sa_damping IS NULL)))
) TABLESPACE hzrdr_ts;

CREATE TABLE hzrdr.gmf_node (
    id SERIAL PRIMARY KEY,
    gmf_id INTEGER NOT NULL,  -- FK to gmf.id
    iml float NOT NULL
) TABLESPACE hzrdr_ts;
SELECT AddGeometryColumn('hzrdr', 'gmf_node', 'location', 4326, 'POINT', 2);
ALTER TABLE hzrdr.gmf_node ALTER COLUMN location SET NOT NULL;


-- GMF data.
-- TODO: DEPRECATED; use gmf_collection, gmf_set, gmf, and gmf_node
CREATE TABLE hzrdr.gmf_data (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    -- Ground motion value
    ground_motion float NOT NULL
) TABLESPACE hzrdr_ts;
SELECT AddGeometryColumn('hzrdr', 'gmf_data', 'location', 4326, 'POINT', 2);
ALTER TABLE hzrdr.gmf_data ALTER COLUMN location SET NOT NULL;


-- Uniform Hazard Spectra
--
-- A collection of Uniform Hazard Spectrum which share a set of periods.
-- A UH Spectrum has a PoE (Probability of Exceedence) and is conceptually
-- composed of a set of 2D matrices, 1 matrix per site/point of interest.
-- Each 2D matrix has a number of rows equal to `realizations` and a number of
-- columns equal to the number of `periods`.
CREATE TABLE hzrdr.uh_spectra (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    timespan float NOT NULL CONSTRAINT valid_uhs_timespan
        CHECK (timespan > 0.0),
    realizations INTEGER NOT NULL CONSTRAINT uh_spectra_realizations_is_set
        CHECK (realizations >= 1),
    -- There should be at least 1 period value defined.
    periods float[] NOT NULL CONSTRAINT uh_spectra_periods_is_set
        CHECK ((periods <> '{}'))
) TABLESPACE hzrdr_ts;


-- Uniform Hazard Spectrum
--
-- * "Uniform" meaning "the same PoE"
-- * "Spectrum" because it covers a range/band of periods/frequencies
CREATE TABLE hzrdr.uh_spectrum (
    id SERIAL PRIMARY KEY,
    uh_spectra_id INTEGER NOT NULL,
    poe float NOT NULL CONSTRAINT uh_spectrum_poe_is_set
        CHECK ((poe >= 0.0) AND (poe <= 1.0))
) TABLESPACE hzrdr_ts;


-- Uniform Hazard Spectrum Data
--
-- A single "row" of data in a UHS matrix for a specific site/point of interest.
CREATE TABLE hzrdr.uh_spectrum_data (
    id SERIAL PRIMARY KEY,
    uh_spectrum_id INTEGER NOT NULL, -- Unique -> (uh_spectrum_id, realization, location)
    -- logic tree sample number for this calculation result,
    -- from 0 to N
    realization INTEGER NOT NULL,
    sa_values float[] NOT NULL CONSTRAINT sa_values_is_set
        CHECK ((sa_values <> '{}'))
) TABLESPACE hzrdr_ts;
SELECT AddGeometryColumn('hzrdr', 'uh_spectrum_data', 'location', 4326, 'POINT', 2);
ALTER TABLE hzrdr.uh_spectrum_data ALTER COLUMN location SET NOT NULL;


-- keep track of logic tree realization progress for a given calculation
CREATE TABLE hzrdr.lt_realization (
    id SERIAL PRIMARY KEY,
    hazard_calculation_id INTEGER NOT NULL,
    -- pre-computed calculation point of interest to site parameters table
    -- can be null if no site_model was defined for the calculation
    site_data_id INTEGER,
    ordinal INTEGER NOT NULL,
    -- random seed number, used only for monte-carlo sampling of logic trees
    seed INTEGER,
    -- path weight, used only for full paths enumeration
    weight NUMERIC CONSTRAINT seed_weight_xor
        CHECK ((seed IS NULL AND weight IS NOT NULL)
               OR (seed IS NOT NULL AND weight IS NULL)),
    -- A list of the logic tree branchIDs which indicate the path taken through the tree
    sm_lt_path VARCHAR[] NOT NULL,
    -- A list of the logic tree branchIDs which indicate the path taken through the tree
    gsim_lt_path VARCHAR[] NOT NULL,
    is_complete BOOLEAN DEFAULT FALSE,
    total_sources INTEGER NOT NULL,
    completed_sources INTEGER NOT NULL DEFAULT 0
) TABLESPACE hzrdr_ts;


-- Loss map data.
CREATE TABLE riskr.loss_map (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    scenario BOOLEAN NOT NULL,
    loss_map_ref VARCHAR,
    end_branch_label VARCHAR,
    category VARCHAR,
    unit VARCHAR, -- e.g. USD, EUR
    timespan float CONSTRAINT valid_timespan
        CHECK (timespan > 0.0),
    -- poe is significant only for non-scenario calculations
    poe float CONSTRAINT valid_poe
        CHECK ((NOT scenario AND (poe >= 0.0) AND (poe <= 1.0))
               OR (scenario AND poe IS NULL))
) TABLESPACE riskr_ts;

CREATE TABLE riskr.loss_map_data (
    id SERIAL PRIMARY KEY,
    loss_map_id INTEGER NOT NULL, -- FK to loss_map.id
    asset_ref VARCHAR NOT NULL,
    value float NOT NULL,
    -- for non-scenario calculations std_dev is 0
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


-- Damage Distribution Per Asset
CREATE TABLE riskr.dmg_dist_per_asset (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,  -- FK to uiapi.output.id
    dmg_states VARCHAR[] NOT NULL,
    end_branch_label VARCHAR
) TABLESPACE riskr_ts;

CREATE TABLE riskr.dmg_dist_per_asset_data (
    id SERIAL PRIMARY KEY,
    dmg_dist_per_asset_id INTEGER NOT NULL,  -- FK to riskr.dmg_dist_per_asset.id
    exposure_data_id INTEGER NOT NULL,  -- FK to oqmif.exposure_data.id
    dmg_state VARCHAR NOT NULL,
    mean float NOT NULL,
    stddev float NOT NULL
) TABLESPACE riskr_ts;
SELECT AddGeometryColumn('riskr', 'dmg_dist_per_asset_data', 'location', 4326, 'POINT', 2);
ALTER TABLE riskr.dmg_dist_per_asset_data ALTER COLUMN location SET NOT NULL;


-- Damage Distrubtion Per Taxonomy
CREATE TABLE riskr.dmg_dist_per_taxonomy (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,  -- FK to uiapi.output.id
    dmg_states VARCHAR[] NOT NULL,
    end_branch_label VARCHAR
) TABLESPACE riskr_ts;

CREATE TABLE riskr.dmg_dist_per_taxonomy_data (
    id SERIAL PRIMARY KEY,
    dmg_dist_per_taxonomy_id INTEGER NOT NULL,  -- FK riskr.dmg_dist_per_taxonomy.id
    taxonomy VARCHAR NOT NULL,
    dmg_state VARCHAR NOT NULL,
    mean float NOT NULL,
    stddev float NOT NULL
) TABLESPACE riskr_ts;


-- Total Damage Distribution
CREATE TABLE riskr.dmg_dist_total (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,  -- FK to uiapi.output.id
    dmg_states VARCHAR[] NOT NULL,
    end_branch_label VARCHAR
) TABLESPACE riskr_ts;

CREATE TABLE riskr.dmg_dist_total_data (
    id SERIAL PRIMARY KEY,
    dmg_dist_total_id INTEGER NOT NULL,  -- FK to riskr.dmg_dist_total.id
    dmg_state VARCHAR NOT NULL,
    mean float NOT NULL,
    stddev float NOT NULL
) TABLESPACE riskr_ts;


-- Exposure model
-- Abbreviations:
--      coco: contents cost
--      reco: retrofitting cost
--      stco: structural cost
CREATE TABLE oqmif.exposure_model (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- Associates the risk exposure model with an input file
    input_id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    description VARCHAR,
    -- the taxonomy system used to classify the assets
    taxonomy_source VARCHAR,
    -- e.g. "buildings", "bridges" etc.
    category VARCHAR NOT NULL,

    -- area type
    area_type VARCHAR CONSTRAINT area_type_value
        CHECK(area_type IS NULL OR area_type = 'per_asset'
              OR area_type = 'aggregated'),

    -- area unit
    area_unit VARCHAR,

    -- contents cost type
    coco_type VARCHAR CONSTRAINT coco_type_value
        CHECK(coco_type IS NULL OR coco_type = 'per_asset'
              OR coco_type = 'per_area' OR coco_type = 'aggregated'),
    -- contents cost unit
    coco_unit VARCHAR,

    -- retrofitting cost type
    reco_type VARCHAR CONSTRAINT reco_type_value
        CHECK(reco_type IS NULL OR reco_type = 'per_asset'
              OR reco_type = 'per_area' OR reco_type = 'aggregated'),
    -- retrofitting cost unit
    reco_unit VARCHAR,

    -- structural cost type
    stco_type VARCHAR CONSTRAINT stco_type_value
        CHECK(stco_type IS NULL OR stco_type = 'per_asset'
              OR stco_type = 'per_area' OR stco_type = 'aggregated'),
    -- structural cost unit
    stco_unit VARCHAR,

    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE oqmif_ts;


-- Per-asset exposure data
CREATE TABLE oqmif.exposure_data (
    id SERIAL PRIMARY KEY,
    exposure_model_id INTEGER NOT NULL,
    -- the asset reference is unique within an exposure model.
    asset_ref VARCHAR NOT NULL,

    -- vulnerability function reference
    taxonomy VARCHAR NOT NULL,

    -- structural cost
    stco float CONSTRAINT stco_value CHECK(stco >= 0.0),
    -- retrofitting cost
    reco float CONSTRAINT reco_value CHECK(reco >= 0.0),
    -- contents cost
    coco float CONSTRAINT coco_value CHECK(coco >= 0.0),

    -- number of assets, people etc.
    number_of_units float CONSTRAINT number_of_units_value
        CHECK(number_of_units >= 0.0),
    area float CONSTRAINT area_value CHECK(area >= 0.0),

    -- insurance coverage limit
    ins_limit float,
    -- insurance deductible
    deductible float,

    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL,
    UNIQUE (exposure_model_id, asset_ref)
) TABLESPACE oqmif_ts;
SELECT AddGeometryColumn('oqmif', 'exposure_data', 'site', 4326, 'POINT', 2);
ALTER TABLE oqmif.exposure_data ALTER COLUMN site SET NOT NULL;


CREATE TABLE oqmif.occupancy (
    id SERIAL PRIMARY KEY,
    exposure_data_id INTEGER NOT NULL,
    description VARCHAR NOT NULL,
    occupants INTEGER NOT NULL
) TABLESPACE oqmif_ts;


-- Vulnerability model
CREATE TABLE riski.vulnerability_model (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- Associates the risk vulnerability model with an input file
    input_id INTEGER,
    name VARCHAR NOT NULL,
    description VARCHAR,
    imt VARCHAR NOT NULL CONSTRAINT imt_value
        CHECK(imt IN ('pga', 'sa', 'pgv', 'pgd', 'ia', 'rsd', 'mmi')),
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
    taxonomy VARCHAR NOT NULL,
    -- Please note: there must be one loss ratio and coefficient of variation
    -- per IML value defined in the referenced vulnerability model.
    loss_ratios float[] NOT NULL CONSTRAINT loss_ratio_values
        CHECK (0.0 <= ALL(loss_ratios) AND 1.0 >= ALL(loss_ratios)),
    -- Coefficients of variation
    covs float[] NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL,
    UNIQUE (vulnerability_model_id, taxonomy)
) TABLESPACE riski_ts;


-- Fragility model
CREATE TABLE riski.fragility_model (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- Associates the risk fragility model with an input file
    input_id INTEGER NOT NULL,
    description VARCHAR,
    -- Fragility model format: one of "discrete", "continuous"
    format VARCHAR NOT NULL CONSTRAINT format_value
        CHECK(format IN ('continuous', 'discrete')),
    -- Limit states
    lss VARCHAR[] NOT NULL,
    -- Intensity measure levels, only applicable to discrete fragility models.
    imls float[],
    -- Intensity measure type, only applicable to discrete fragility models.
    imt VARCHAR(16),
    -- IML unit of measurement
    iml_unit VARCHAR(16),
    -- minimum IML value, only applicable to continuous fragility models.
    min_iml float,
    -- maximum IML value, only applicable to continuous fragility models.
    max_iml float,
    -- defines the IML after which damage is observed, only applicable to
    -- discrete fragility models.
    no_damage_limit float,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE riski_ts;


-- Continuous fragility function
CREATE TABLE riski.ffc (
    id SERIAL PRIMARY KEY,
    fragility_model_id INTEGER NOT NULL,
    -- limit state index, facilitates the ordering of fragility functions in
    -- accordance to limit states
    lsi smallint NOT NULL CONSTRAINT lsi_value CHECK(lsi > 0),
    -- limit state
    ls VARCHAR NOT NULL,
    -- taxonomy
    taxonomy VARCHAR NOT NULL,
    -- Optional function/distribution type e.g. lognormal
    ftype VARCHAR,
    mean float NOT NULL,
    stddev float NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL,
    -- The combination of limit state and taxonomy is unique within an
    -- fragility model.
    UNIQUE (fragility_model_id, taxonomy, lsi)
) TABLESPACE riski_ts;


-- Discrete fragility function
CREATE TABLE riski.ffd (
    id SERIAL PRIMARY KEY,
    fragility_model_id INTEGER NOT NULL,
    -- limit state index, facilitates the ordering of fragility functions in
    -- accordance to limit states
    lsi smallint NOT NULL CONSTRAINT lsi_value CHECK(lsi > 0),
    -- limit state
    ls VARCHAR NOT NULL,
    -- taxonomy
    taxonomy VARCHAR NOT NULL,
    poes float[] NOT NULL CONSTRAINT poes_values
        CHECK (0.0 <= ALL(poes) AND 1.0 >= ALL(poes)),
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL,
    -- The combination of limit state and taxonomy is unique within an
    -- fragility model.
    UNIQUE (fragility_model_id, taxonomy, lsi)
) TABLESPACE riski_ts;


-- keep track of sources considered in a calculation, per logic tree realization
CREATE TABLE htemp.source_progress (
    id SERIAL PRIMARY KEY,
    lt_realization_id INTEGER NOT NULL,
    parsed_source_id INTEGER NOT NULL,
    is_complete BOOLEAN NOT NULL DEFAULT FALSE
) TABLESPACE htemp_ts;

CREATE TABLE htemp.hazard_curve_progress (
    -- This table will contain 1 record per IMT per logic tree realization
    -- for a given calculation.
    id SERIAL PRIMARY KEY,
    lt_realization_id INTEGER NOT NULL,
    imt VARCHAR NOT NULL,
    -- stores a pickled numpy array for intermediate results
    -- array is 2d: sites x IMLs
    -- each row indicates a site,
    -- each column holds the PoE value for the IML at that index
    result_matrix BYTEA NOT NULL
) TABLESPACE htemp_ts;

CREATE TABLE htemp.site_data (
    id SERIAL PRIMARY KEY,
    hazard_calculation_id INTEGER NOT NULL,
    -- All 6 fields will contain pickled numpy arrays with all of the locations
    -- and site parameters for the sites of interest for a calculation.
    lons BYTEA NOT NULL,
    lats BYTEA NOT NULL,
    vs30s BYTEA NOT NULL,
    vs30_measured BYTEA NOT NULL,
    z1pt0s BYTEA NOT NULL,
    z2pt5s BYTEA NOT NULL
) TABLESPACE htemp_ts;


------------------------------------------------------------------------
-- Constraints (foreign keys etc.) go here
------------------------------------------------------------------------
ALTER TABLE admin.oq_user ADD CONSTRAINT admin_oq_user_organization_fk
FOREIGN KEY (organization_id) REFERENCES admin.organization(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.site_model ADD CONSTRAINT hzrdi_site_model_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.parsed_source ADD CONSTRAINT hzrdi_parsed_source_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE RESTRICT;

ALTER TABLE eqcat.catalog ADD CONSTRAINT eqcat_catalog_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE eqcat.catalog ADD CONSTRAINT eqcat_catalog_magnitude_fk
FOREIGN KEY (magnitude_id) REFERENCES eqcat.magnitude(id) ON DELETE RESTRICT;

ALTER TABLE eqcat.catalog ADD CONSTRAINT eqcat_catalog_surface_fk
FOREIGN KEY (surface_id) REFERENCES eqcat.surface(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.oq_job ADD CONSTRAINT uiapi_oq_job_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.oq_job ADD CONSTRAINT uiapi_oq_job_hazard_calculation
FOREIGN KEY (hazard_calculation_id) REFERENCES uiapi.hazard_calculation(id)
ON DELETE RESTRICT;

ALTER TABLE uiapi.hazard_calculation ADD CONSTRAINT uiapi_hazard_calculation_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.input2hcalc ADD CONSTRAINT uiapi_input2hcalc_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.input2hcalc ADD CONSTRAINT uiapi_input2hcalc_hazard_calculation_fk
FOREIGN KEY (hazard_calculation_id) REFERENCES uiapi.hazard_calculation(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.oq_job_profile ADD CONSTRAINT uiapi_oq_job_profile_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.job_stats ADD CONSTRAINT  uiapi_job_stats_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

ALTER TABLE uiapi.input2job ADD CONSTRAINT  uiapi_input2job_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE CASCADE;

ALTER TABLE uiapi.input2job ADD CONSTRAINT  uiapi_input2job_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

ALTER TABLE uiapi.src2ltsrc ADD CONSTRAINT  uiapi_src2ltsrc_src_fk
FOREIGN KEY (hzrd_src_id) REFERENCES uiapi.input(id) ON DELETE CASCADE;

ALTER TABLE uiapi.src2ltsrc ADD CONSTRAINT  uiapi_src2ltsrc_ltsrc_fk
FOREIGN KEY (lt_src_id) REFERENCES uiapi.input(id) ON DELETE CASCADE;

ALTER TABLE uiapi.job2profile ADD CONSTRAINT
uiapi_job2profile_oq_job_profile_fk FOREIGN KEY (oq_job_profile_id) REFERENCES
uiapi.oq_job_profile(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.job2profile ADD CONSTRAINT uiapi_job2profile_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

ALTER TABLE uiapi.input2upload ADD CONSTRAINT uiapi_input2upload_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE CASCADE;

ALTER TABLE uiapi.input2upload ADD CONSTRAINT uiapi_input2upload_upload_fk
FOREIGN KEY (upload_id) REFERENCES uiapi.upload(id) ON DELETE CASCADE;

ALTER TABLE uiapi.upload ADD CONSTRAINT uiapi_upload_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.input ADD CONSTRAINT uiapi_input_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.input ADD CONSTRAINT uiapi_input_model_content_fk
FOREIGN KEY (model_content_id) REFERENCES uiapi.model_content(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.output ADD CONSTRAINT uiapi_output_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.output ADD CONSTRAINT uiapi_output_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.error_msg ADD CONSTRAINT uiapi_error_msg_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

ALTER TABLE oqmif.exposure_model ADD CONSTRAINT oqmif_exposure_model_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE oqmif.exposure_model ADD CONSTRAINT oqmif_exposure_model_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE RESTRICT;

ALTER TABLE riski.vulnerability_model ADD CONSTRAINT
riski_vulnerability_model_owner_fk FOREIGN KEY (owner_id) REFERENCES
admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE riski.fragility_model ADD CONSTRAINT
riski_fragility_model_owner_fk FOREIGN KEY (owner_id) REFERENCES
admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE riski.vulnerability_model ADD CONSTRAINT
riski_vulnerability_model_input_fk FOREIGN KEY (input_id) REFERENCES
uiapi.input(id) ON DELETE RESTRICT;

ALTER TABLE riski.fragility_model ADD CONSTRAINT
riski_fragility_model_input_fk FOREIGN KEY (input_id) REFERENCES
uiapi.input(id) ON DELETE RESTRICT;

ALTER TABLE hzrdr.hazard_map
ADD CONSTRAINT hzrdr_hazard_map_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE hzrdr.hazard_map_data
ADD CONSTRAINT hzrdr_hazard_map_data_hazard_map_fk
FOREIGN KEY (hazard_map_id) REFERENCES hzrdr.hazard_map(id) ON DELETE CASCADE;

ALTER TABLE hzrdr.hazard_curve
ADD CONSTRAINT hzrdr_hazard_curve_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE hzrdr.hazard_curve
ADD CONSTRAINT hzrdr_hazard_curve_lt_realization_fk
FOREIGN KEY (lt_realization_id) REFERENCES hzrdr.lt_realization(id)
ON DELETE RESTRICT;

ALTER TABLE hzrdr.hazard_curve_data
ADD CONSTRAINT hzrdr_hazard_curve_data_hazard_curve_fk
FOREIGN KEY (hazard_curve_id) REFERENCES hzrdr.hazard_curve(id) ON DELETE CASCADE;

ALTER TABLE hzrdr.gmf_data
ADD CONSTRAINT hzrdr_gmf_data_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

-- gmf_collection -> output FK
ALTER TABLE hzrdr.gmf_collection
ADD CONSTRAINT hzrdr_gmf_collection_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

-- gmf_collection -> lt_realization FK
ALTER TABLE hzrdr.gmf_collection
ADD CONSTRAINT hzrdr_gmf_collection_lt_realization_fk
FOREIGN KEY (lt_realization_id) REFERENCES hzrdr.lt_realization(id)
ON DELETE RESTRICT;

-- gmf_set -> gmf_collection FK
ALTER TABLE hzrdr.gmf_set
ADD CONSTRAINT hzrdr_gmf_set_gmf_collection_fk
FOREIGN KEY (gmf_collection_id) REFERENCES hzrdr.gmf_collection(id)
ON DELETE CASCADE;

-- gmf -> gmf_set FK
ALTER TABLE hzrdr.gmf
ADD CONSTRAINT hzrdr_gmf_gmf_set_fk
FOREIGN KEY (gmf_set_id) REFERENCES hzrdr.gmf_set(id)
ON DELETE CASCADE;

-- gmf_node -> gmf FK
ALTER TABLE hzrdr.gmf_node
ADD CONSTRAINT hzrdr_gmf_node_gmf_fk
FOREIGN KEY (gmf_id) REFERENCES hzrdr.gmf(id)
ON DELETE CASCADE;


-- UHS:
-- uh_spectra -> output FK
ALTER TABLE hzrdr.uh_spectra
ADD CONSTRAINT hzrdr_uh_spectra_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

-- uh_spectrum -> uh_spectra FK
ALTER TABLE hzrdr.uh_spectrum
ADD CONSTRAINT hzrdr_uh_spectrum_uh_spectra_fk
FOREIGN KEY (uh_spectra_id) REFERENCES hzrdr.uh_spectra(id) ON DELETE CASCADE;

-- uh_spectrum_data -> uh_spectrum FK
ALTER TABLE hzrdr.uh_spectrum_data
ADD CONSTRAINT hzrdr_uh_spectrum_data_uh_spectrum_fk
FOREIGN KEY (uh_spectrum_id) REFERENCES hzrdr.uh_spectrum(id) ON DELETE CASCADE;

-- hzrdr.lt_realization -> uiapi.hazard_calculation FK
ALTER TABLE hzrdr.lt_realization
ADD CONSTRAINT hzrdr_lt_realization_hazard_calculation_fk
FOREIGN KEY (hazard_calculation_id)
REFERENCES uiapi.hazard_calculation(id)
ON DELETE CASCADE;

-- hzrdr.ses_collection to uiapi.output FK
ALTER TABLE hzrdr.ses_collection
ADD CONSTRAINT hzrdr_ses_collection_output_fk
FOREIGN KEY (output_id)
REFERENCES uiapi.output(id)
ON DELETE CASCADE;

-- hzrdr.ses_collection to hzrdr.lt_realization FK
ALTER TABLE hzrdr.ses_collection
ADD CONSTRAINT hzrdr_ses_collection_lt_realization_fk
FOREIGN KEY (lt_realization_id)
REFERENCES hzrdr.lt_realization(id)
ON DELETE RESTRICT;

-- hzrdr.ses to hzrdr.ses_collection FK
ALTER TABLE hzrdr.ses
ADD CONSTRAINT hzrdr_ses_ses_collection_fk
FOREIGN KEY (ses_collection_id)
REFERENCES hzrdr.ses_collection(id)
ON DELETE CASCADE;

-- hzrdr.ses_rupture to hzrdr.ses FK
ALTER TABLE hzrdr.ses_rupture
ADD CONSTRAINT hzrdr_ses_rupture_ses_fk
FOREIGN KEY (ses_id)
REFERENCES hzrdr.ses(id)
ON DELETE CASCADE;

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


-- Damage Distribution, Per Asset
ALTER TABLE riskr.dmg_dist_per_asset
ADD CONSTRAINT riskr_dmg_dist_per_asset_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.dmg_dist_per_asset_data
ADD CONSTRAINT riskr_dmg_dist_per_asset_data_dmg_dist_per_asset_fk
FOREIGN KEY (dmg_dist_per_asset_id) REFERENCES riskr.dmg_dist_per_asset(id) ON DELETE CASCADE;

ALTER TABLE riskr.dmg_dist_per_asset_data
ADD CONSTRAINT riskr_dmg_dist_per_asset_data_exposure_data_fk
FOREIGN KEY (exposure_data_id) REFERENCES oqmif.exposure_data(id) ON DELETE RESTRICT;


-- Damage Distribution, Per Taxonomy
ALTER TABLE riskr.dmg_dist_per_taxonomy
ADD CONSTRAINT riskr_dmg_dist_per_taxonomy_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.dmg_dist_per_taxonomy_data
ADD CONSTRAINT riskr_dmg_dist_per_taxonomy_data_dmg_dist_per_taxonomy_fk
FOREIGN KEY (dmg_dist_per_taxonomy_id) REFERENCES riskr.dmg_dist_per_taxonomy(id) ON DELETE CASCADE;


-- Damage Distribution, Total
ALTER TABLE riskr.dmg_dist_total
ADD CONSTRAINT riskr_dmg_dist_total_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.dmg_dist_total_data
ADD CONSTRAINT riskr_dmg_dist_total_data_dmg_dist_total_fk
FOREIGN KEY (dmg_dist_total_id) REFERENCES riskr.dmg_dist_total(id) ON DELETE CASCADE;

ALTER TABLE oqmif.exposure_data ADD CONSTRAINT
oqmif_exposure_data_exposure_model_fk FOREIGN KEY (exposure_model_id)
REFERENCES oqmif.exposure_model(id) ON DELETE CASCADE;

ALTER TABLE oqmif.occupancy ADD CONSTRAINT
oqmif_occupancy_exposure_data_fk FOREIGN KEY (exposure_data_id)
REFERENCES oqmif.exposure_data(id) ON DELETE CASCADE;

ALTER TABLE riski.vulnerability_function ADD CONSTRAINT
riski_vulnerability_function_vulnerability_model_fk FOREIGN KEY
(vulnerability_model_id) REFERENCES riski.vulnerability_model(id) ON DELETE
CASCADE;

ALTER TABLE riski.ffd ADD CONSTRAINT riski_ffd_fragility_model_fk FOREIGN KEY
(fragility_model_id) REFERENCES riski.fragility_model(id) ON DELETE
CASCADE;

ALTER TABLE riski.ffc ADD CONSTRAINT riski_ffc_fragility_model_fk FOREIGN KEY
(fragility_model_id) REFERENCES riski.fragility_model(id) ON DELETE
CASCADE;


-- htemp.source_progress to hzrdr.lt_realization FK
ALTER TABLE htemp.source_progress
ADD CONSTRAINT htemp_source_progress_lt_realization_fk
FOREIGN KEY (lt_realization_id)
REFERENCES hzrdr.lt_realization(id)
ON DELETE CASCADE;

-- htemp.source_progress to hzrdi.parsed_source FK
ALTER TABLE htemp.source_progress
ADD CONSTRAINT htemp_source_progress_parsed_source_fk
FOREIGN KEY (parsed_source_id)
REFERENCES hzrdi.parsed_source(id)
ON DELETE CASCADE;

-- htemp.hazard_curve_progress to hzrdr.lt_realization FK
ALTER TABLE htemp.hazard_curve_progress
ADD CONSTRAINT htemp_hazard_curve_progress_lt_realization_fk
FOREIGN KEY (lt_realization_id)
REFERENCES hzrdr.lt_realization(id)
ON DELETE CASCADE;

-- htemp.site_data to uiapi.hazard_calculation FK
ALTER TABLE htemp.site_data
ADD CONSTRAINT htemp_site_data_hazard_calculation_fk
FOREIGN KEY (hazard_calculation_id)
REFERENCES uiapi.hazard_calculation(id)
ON DELETE CASCADE;
