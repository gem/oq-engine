/*
  OpenQuake database schema definitions.

    Copyright (c) 2010-2012, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- Disable unnecessarily verbose output
SET client_min_messages TO WARNING;

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
        (source_type IN ('area', 'point', 'complex', 'simple', 'characteristic')),
    nrml BYTEA NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE hzrdi_ts;


-- Parsed Rupture models
CREATE TABLE hzrdi.parsed_rupture_model (
    id SERIAL PRIMARY KEY,
    input_id INTEGER NOT NULL,
    rupture_type VARCHAR NOT NULL
        CONSTRAINT enforce_rupture_type CHECK
        (rupture_type IN ('complex_fault', 'simple_fault')),
    nrml BYTEA NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE hzrdi_ts;


-- A single OpenQuake input file imported by the user
CREATE TABLE uiapi.input (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    model_content_id INTEGER,
    -- Optional name for the input.
    name VARCHAR,
    -- The full path of the input file on the server
    path VARCHAR NOT NULL,
    digest VARCHAR(32) NOT NULL,
    -- Input file type, one of:
    --      source model file (source)
    --      source logic tree (source_model_logic_tree)
    --      GSIM logic tree (gsim_logic_tree)
    --      exposure file (exposure)
    --      vulnerability file (vulnerability)
    --      rupture file (rupture)
    input_type VARCHAR NOT NULL CONSTRAINT input_type_value
        CHECK(input_type IN ('unknown', 'source', 'source_model_logic_tree', 'gsim_logic_tree',
                             'exposure', 'fragility', 'rupture_model',
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
    risk_calculation_id INTEGER,  -- FK to uiapi.risk_calculation
    log_level VARCHAR NOT NULL DEFAULT 'progress' CONSTRAINT oq_job_log_level_check
        CHECK(log_level IN ('debug', 'info', 'progress', 'warn', 'error', 'critical')),
    -- One of: pre_execution, executing, post_execution, post_processing, complete
    status VARCHAR NOT NULL DEFAULT 'pre_executing' CONSTRAINT job_status_value
        CHECK(status IN ('pre_executing', 'executing', 'post_executing',
                         'post_processing', 'export', 'clean_up', 'complete')),
    oq_version VARCHAR,
    hazardlib_version VARCHAR,
    nrml_version VARCHAR,
    is_running BOOLEAN NOT NULL DEFAULT FALSE,
    duration INTEGER NOT NULL DEFAULT 0,
    job_pid INTEGER NOT NULL DEFAULT 0,
    supervisor_pid INTEGER NOT NULL DEFAULT 0,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;


-- Tracks task performance
CREATE TABLE uiapi.performance (
    id SERIAL PRIMARY KEY,
    oq_job_id INTEGER NOT NULL,
    task_id VARCHAR,
    start_time timestamp without time zone NOT NULL,
    task VARCHAR,
    operation VARCHAR NOT NULL,
    duration FLOAT,
    pymemory INTEGER,
    pgmemory INTEGER
)  TABLESPACE uiapi_ts;


-- Tracks various job statistics
CREATE TABLE uiapi.job_stats (
    id SERIAL PRIMARY KEY,
    oq_job_id INTEGER NOT NULL,
    start_time timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL,
    stop_time timestamp without time zone,
    -- The number of total sites in the calculation
    num_sites INTEGER,
    -- The number of tasks in a job
    num_tasks INTEGER,
    -- The number of logic tree samples
    num_realizations INTEGER
) TABLESPACE uiapi_ts;


-- how long are the various job phases taking?
CREATE TABLE uiapi.job_phase_stats (
    id SERIAL PRIMARY KEY,
    oq_job_id INTEGER NOT NULL,
    -- calculation type (hazard|risk)
    ctype VARCHAR NOT NULL,
    job_status VARCHAR NOT NULL,
    start_time timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL,
    UNIQUE (oq_job_id, ctype, job_status)
) TABLESPACE uiapi_ts;


CREATE TABLE uiapi.hazard_calculation (
    -- TODO(larsbutler): At the moment, this model only contains Classical
    -- hazard parameters.
    -- We'll need to update fields and constraints as we add the other
    -- calculation modes.
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- Contains the absolute path to the directory containing the job config
    -- file
    base_path VARCHAR NOT NULL,
    export_dir VARCHAR,
    -- general parameters:
    -- (see also `region` and `sites` geometries defined below)
    description VARCHAR NOT NULL DEFAULT '',
    -- what time period w/o any progress is acceptable for calculations?
    -- The timeout is stored in seconds and is 1 hour by default.
    no_progress_timeout INTEGER NOT NULL DEFAULT 3600,
    calculation_mode VARCHAR NOT NULL CONSTRAINT haz_calc_mode
        CHECK(calculation_mode IN (
            'classical',
            'event_based',
            'disaggregation',
            'scenario'
        )),
    region_grid_spacing float,
    -- a pickled `openquake.hazardlib.site.SiteCollection` object
    site_collection BYTEA,
    -- logic tree parameters:
    random_seed INTEGER,
    number_of_logic_tree_samples INTEGER,
    -- ERF parameters:
    rupture_mesh_spacing float,
    width_of_mfd_bin float,
    area_source_discretization float,
    -- site parameters:
    reference_vs30_value float,
    reference_vs30_type VARCHAR CONSTRAINT vs30_type
        CHECK(((reference_vs30_type IS NULL)
               OR
               (reference_vs30_type IN ('measured', 'inferred')))),
    reference_depth_to_2pt5km_per_sec float,
    reference_depth_to_1pt0km_per_sec float,
    -- calculation parameters:
    investigation_time float,
    intensity_measure_types_and_levels bytea NOT NULL,  -- stored as a pickled Python `dict`
    truncation_level float,
    maximum_distance float NOT NULL,
    -- event-based calculator parameters:
    intensity_measure_types VARCHAR[],
    ses_per_logic_tree_path INTEGER,
    ground_motion_correlation_model VARCHAR,
    ground_motion_correlation_params bytea, -- stored as a pickled Python `dict`
    -- scenario calculator parameters:
    gsim VARCHAR,
    number_of_ground_motion_fields INTEGER,
    -- disaggregation calculator parameters:
    mag_bin_width float,
    distance_bin_width float,
    coordinate_bin_width float,
    num_epsilon_bins INTEGER,
    poes_disagg float[],
    -- output/post-processing parameters:
    -- classical:
    mean_hazard_curves boolean DEFAULT false,
    quantile_hazard_curves float[],
    poes float[],
    hazard_maps boolean DEFAULT false,
    uniform_hazard_spectra boolean DEFAULT false,
    export_multi_curves boolean DEFAULT false,
    -- event-based:
    complete_logic_tree_ses BOOLEAN,
    complete_logic_tree_gmf BOOLEAN,
    ground_motion_fields BOOLEAN,
    hazard_curves_from_gmfs BOOLEAN
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'hazard_calculation', 'region', 4326, 'POLYGON', 2);
SELECT AddGeometryColumn('uiapi', 'hazard_calculation', 'sites', 4326, 'MULTIPOINT', 2);


CREATE TABLE uiapi.input2hcalc (
    id SERIAL PRIMARY KEY,
    input_id INTEGER NOT NULL,
    hazard_calculation_id INTEGER NOT NULL
) TABLESPACE uiapi_ts;


CREATE TABLE uiapi.input2rcalc (
    id SERIAL PRIMARY KEY,
    input_id INTEGER NOT NULL,
    risk_calculation_id INTEGER NOT NULL
) TABLESPACE uiapi_ts;


CREATE TABLE uiapi.risk_calculation (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,  -- FK to admin.oq_user
    -- Contains the absolute path to the directory containing the job config
    -- file
    base_path VARCHAR NOT NULL,
    export_dir VARCHAR,
    -- general parameters:
    description VARCHAR NOT NULL DEFAULT '',
    -- what time period w/o any progress is acceptable for calculations?
    -- The timeout is stored in seconds and is 1 hour by default.
    no_progress_timeout INTEGER NOT NULL DEFAULT 3600,
    calculation_mode VARCHAR NOT NULL,

    maximum_distance FLOAT NULL,

    exposure_input_id INTEGER,

    hazard_output_id INTEGER NULL,  -- FK to uiapi.output
    hazard_calculation_id INTEGER NULL,  -- FK to uiapi.hazard_calculation

    mean_loss_curves boolean DEFAULT false,
    quantile_loss_curves float[],
    conditional_loss_poes float[],

    poes_disagg float[],

    taxonomies_from_model BOOLEAN,

    -- probabilistic parameters
    asset_correlation float NULL
    CONSTRAINT asset_correlation_value
    CHECK (
      (asset_correlation IS NULL) OR
      ((asset_correlation >= 0) AND (asset_correlation <= 1))),
    master_seed INTEGER NULL,

    mag_bin_width float,
    distance_bin_width float,
    coordinate_bin_width float,

    -- classical parameters:
    lrem_steps_per_interval INTEGER,

    -- event-based parameters:
    loss_curve_resolution INTEGER NOT NULL DEFAULT 50
        CONSTRAINT loss_curve_resolution_is_set
        CHECK  (loss_curve_resolution >= 1),
    insured_losses BOOLEAN DEFAULT false,

    -- BCR (Benefit-Cost Ratio) parameters:
    interest_rate float,
    asset_life_expectancy float

) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'risk_calculation', 'region_constraint', 4326, 'POLYGON', 2);
SELECT AddGeometryColumn('uiapi', 'risk_calculation', 'sites_disagg', 4326, 'MULTIPOINT', 2);

CREATE TABLE uiapi.cnode_stats (
    id SERIAL PRIMARY KEY,
    oq_job_id INTEGER NOT NULL,
    node VARCHAR NOT NULL,
    current_status VARCHAR NOT NULL CONSTRAINT current_status_value
        CHECK(current_status IN ('up', 'down')),
    current_ts timestamp without time zone NOT NULL,
    previous_ts timestamp without time zone,
    failures INTEGER NOT NULL DEFAULT 0
) TABLESPACE uiapi_ts;


-- The parameters needed for an OpenQuake engine run
CREATE TABLE uiapi.oq_job_profile (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
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
    oq_job_id INTEGER,
    -- The full path of the output file on the server, optional and only set
    -- for outputs with NRML/XML files.
    display_name VARCHAR NOT NULL,
    output_type VARCHAR NOT NULL CONSTRAINT output_type_value
        CHECK(output_type IN (
            'agg_loss_curve',
            'aggregate_loss',
            'bcr_distribution',
            'collapse_map',
            'complete_lt_gmf',
            'complete_lt_ses',
            'disagg_matrix',
            'dmg_dist_per_asset',
            'dmg_dist_per_taxonomy',
            'dmg_dist_total',
            'event_loss',
            'gmf',
            'gmf_scenario',
            'hazard_curve',
            'hazard_curve_multi',
            'hazard_map',
            'loss_curve',
            'loss_fraction',
            'loss_map',
            'ses',
            'uh_spectra',
            'unknown'
        )),
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


-- Associate an 'source_model_logic_tree' type input (a logic tree source) with 'source'
-- type inputs (hazard sources referenced by the logic tree source).
-- This is needed for worker-side logic tree processing.
CREATE TABLE uiapi.src2ltsrc (
    id SERIAL PRIMARY KEY,
    -- foreign key to the input of type 'source'
    hzrd_src_id INTEGER NOT NULL,
    -- foreign key to the input of type 'source_model_logic_tree'
    lt_src_id INTEGER NOT NULL,
    -- Due to input file reuse, the original file name may deviate from
    -- the current. We hence need to capture the latter.
    filename VARCHAR NOT NULL,
    UNIQUE (hzrd_src_id, lt_src_id)
) TABLESPACE uiapi_ts;


-- Associate jobs and their profiles, a job may be associated with one profile
-- only.
CREATE TABLE uiapi.job2profile (
    id SERIAL PRIMARY KEY,
    oq_job_id INTEGER NOT NULL,
    oq_job_profile_id INTEGER NOT NULL,
    UNIQUE (oq_job_id)
) TABLESPACE uiapi_ts;


-- Complete hazard map
CREATE TABLE hzrdr.hazard_map (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    lt_realization_id INTEGER,  -- lt_realization FK, only required for non-statistical curves
    investigation_time float NOT NULL,
    imt VARCHAR NOT NULL CONSTRAINT hazard_map_imt
        CHECK(imt in ('PGA', 'PGV', 'PGD', 'SA', 'IA', 'RSD', 'MMI')),
    statistics VARCHAR CONSTRAINT hazard_map_statistics
        CHECK(statistics IS NULL OR
              statistics IN ('mean', 'quantile')),
    -- Quantile value (only for "quantile" statistics)
    quantile float CONSTRAINT hazard_map_quantile_value
        CHECK(
            ((statistics = 'quantile') AND (quantile IS NOT NULL))
            OR (((statistics != 'quantile') AND (quantile IS NULL)))),
    sa_period float CONSTRAINT hazard_map_sa_period
        CHECK(
            ((imt = 'SA') AND (sa_period IS NOT NULL))
            OR ((imt != 'SA') AND (sa_period IS NULL))),
    sa_damping float CONSTRAINT hazard_map_sa_damping
        CHECK(
            ((imt = 'SA') AND (sa_damping IS NOT NULL))
            OR ((imt != 'SA') AND (sa_damping IS NULL))),
    poe float NOT NULL,
    lons bytea NOT NULL,
    lats bytea NOT NULL,
    imls bytea NOT NULL
) TABLESPACE hzrdr_ts;


-- Hazard curve data.
CREATE TABLE hzrdr.hazard_curve (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    lt_realization_id INTEGER,  -- lt_realization FK, only required for non-statistical curves
    investigation_time float NOT NULL,
    -- imt and imls might be null if hazard curve is the container for multiple hazard curve set
    imt VARCHAR NULL CONSTRAINT hazard_curve_imt
        CHECK(imt in ('PGA', 'PGV', 'PGD', 'SA', 'IA', 'RSD', 'MMI')),
    imls float[] NULL,
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
    poes float[] NOT NULL,
    -- Copied from hzrdr.lt_realization.
    -- This was added for performance reasons, so we can get the weight
    -- without having to join `hzrdr.lt_realization`.
    -- `weight` can be null, if the weight is implicit.
    weight NUMERIC
) TABLESPACE hzrdr_ts;
SELECT AddGeometryColumn('hzrdr', 'hazard_curve_data', 'location', 4326, 'POINT', 2);
ALTER TABLE hzrdr.hazard_curve_data ALTER COLUMN location SET NOT NULL;


-- Stochastic Event Set Collection
-- A container for all of the Stochastic Event Sets in a given
-- logic tree realization.
CREATE TABLE hzrdr.ses_collection (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    -- If `lt_realization_id` is NULL, this is a `complete logic tree`
    -- Stochastic Event Set Collection, containing a single stochastic
    -- event set containing all of the ruptures from the entire
    -- calculation.
    lt_realization_id INTEGER
) TABLESPACE hzrdr_ts;

-- Stochastic Event Set: A container for 1 or more ruptures associated with a
-- specific investigation time span.
CREATE TABLE hzrdr.ses (
    id SERIAL PRIMARY KEY,
    ses_collection_id INTEGER NOT NULL,
    investigation_time float NOT NULL,
    -- Order number of this Stochastic Event Set in a series of SESs
    -- (for a given logic tree realization).
    ordinal INTEGER
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
    is_multi_surface BOOLEAN NOT NULL,
    lons BYTEA NOT NULL,
    lats BYTEA NOT NULL,
    depths BYTEA NOT NULL,
    surface BYTEA NOT NULL,
    result_grp_ordinal INTEGER NOT NULL,
    -- The sequence number of the rupture within a given task/result group
    rupture_ordinal INTEGER NOT NULL
) TABLESPACE hzrdr_ts;


CREATE TABLE hzrdr.gmf_collection (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,  -- FK to output.id
    -- FK to lt_realization.id
    lt_realization_id INTEGER
) TABLESPACE hzrdr_ts;

CREATE TABLE hzrdr.gmf_set (
    id SERIAL PRIMARY KEY,
    gmf_collection_id INTEGER NOT NULL,  -- FK to gmf_collection.id
    investigation_time float NOT NULL,
    -- Keep track of the stochastic event set which this GMF set is associated with
    ses_ordinal INTEGER
) TABLESPACE hzrdr_ts;

-- This table stores ground motion values. Given an hazard calculation
-- (with calculation_mode equal to event based) we generate a
-- gmf_collection for each logic tree realization considered plus
-- (optionally) a complete_gmf_collection.

-- for each gmf_collection (associated with a realization) we generate
-- a gmf_set for each stochastic event set generated by the hazard
-- calculation. For each gmf_set and for each location we generate a
-- gmf row containing all the ground motion values for all the
-- different ruptures generated.
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
            OR ((imt != 'SA') AND (sa_damping IS NULL))),
    gmvs float[],
-- a vector of ids to the hzrdr.ses_rupture table. for each id you can
-- find the corresponding ground motion value in gmvs at the same
-- index.
    rupture_ids int[],
    result_grp_ordinal INTEGER NOT NULL,

    location GEOGRAPHY(point) NOT NULL
) TABLESPACE hzrdr_ts;


CREATE TABLE hzrdr.gmf_scenario (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,  -- FK to output.id
    imt VARCHAR NOT NULL,
    gmvs float[],
    location GEOGRAPHY(point) NOT NULL,
    UNIQUE (output_id, imt, location)
) TABLESPACE hzrdr_ts;


CREATE TABLE hzrdr.disagg_result (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,  -- FK to uiapi.output
    lt_realization_id INTEGER NOT NULL,  -- FK to hzrdr.lt_realization
    investigation_time float NOT NULL,
    imt VARCHAR NOT NULL CONSTRAINT disagg_result_imt
        CHECK(imt in ('PGA', 'PGV', 'PGD', 'SA', 'IA', 'RSD', 'MMI')),
    iml float NOT NULL,
    poe float NOT NULL,
    sa_period float CONSTRAINT disagg_result_sa_period
        CHECK(
            ((imt = 'SA') AND (sa_period IS NOT NULL))
            OR ((imt != 'SA') AND (sa_period IS NULL))),
    sa_damping float CONSTRAINT disagg_result_sa_damping
        CHECK(
            ((imt = 'SA') AND (sa_damping IS NOT NULL))
            OR ((imt != 'SA') AND (sa_damping IS NULL))),
    mag_bin_edges float[] NOT NULL,
    dist_bin_edges float[] NOT NULL,
    lon_bin_edges float[] NOT NULL,
    lat_bin_edges float[] NOT NULL,
    eps_bin_edges float[] NOT NULL,
    trts VARCHAR[] NOT NULL,
    matrix bytea NOT NULL
) TABLESPACE hzrdr_ts;
SELECT AddGeometryColumn('hzrdr', 'disagg_result', 'location', 4326, 'POINT', 2);
ALTER TABLE hzrdr.disagg_result ALTER COLUMN location SET NOT NULL;


-- GMF data.
-- TODO: DEPRECATED; use gmf_collection, gmf_set, and gmf
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
CREATE TABLE hzrdr.uhs (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    lt_realization_id INTEGER,  -- lt_realization FK, only required for non-statistical curves
    investigation_time float NOT NULL,
    poe float NOT NULL,
    periods float[] NOT NULL,
    statistics VARCHAR CONSTRAINT uhs_statistics
        CHECK(statistics IS NULL OR
              statistics IN ('mean', 'quantile')),
    -- Quantile value (only for "quantile" statistics)
    quantile float CONSTRAINT uhs_quantile_value
        CHECK(
            ((statistics = 'quantile') AND (quantile IS NOT NULL))
            OR (((statistics != 'quantile') AND (quantile IS NULL))))
) TABLESPACE hzrdr_ts;


-- Uniform Hazard Spectrum
--
-- * "Uniform" meaning "the same PoE"
-- * "Spectrum" because it covers a range/band of periods/frequencies
CREATE TABLE hzrdr.uhs_data (
    id SERIAL PRIMARY KEY,
    uhs_id INTEGER NOT NULL,
    imls float[] NOT NULL
) TABLESPACE hzrdr_ts;
SELECT AddGeometryColumn('hzrdr', 'uhs_data', 'location', 4326, 'POINT', 2);
ALTER TABLE hzrdr.uhs_data ALTER COLUMN location SET NOT NULL;


-- keep track of logic tree realization progress for a given calculation
CREATE TABLE hzrdr.lt_realization (
    id SERIAL PRIMARY KEY,
    hazard_calculation_id INTEGER NOT NULL,
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
    total_items INTEGER NOT NULL,
    completed_items INTEGER NOT NULL DEFAULT 0
) TABLESPACE hzrdr_ts;


-- Loss map data.
CREATE TABLE riskr.loss_map (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    hazard_output_id INTEGER NULL,
    insured BOOLEAN NOT NULL DEFAULT false,
    -- poe is significant only for non-scenario calculations
    poe float NULL CONSTRAINT valid_poe
        CHECK (poe IS NULL OR (poe >= 0.0) AND (poe <= 1.0)),
    statistics VARCHAR CONSTRAINT loss_map_statistics
        CHECK(statistics IS NULL OR
              statistics IN ('mean', 'quantile')),
    -- Quantile value (only for "quantile" statistics)
    quantile float CONSTRAINT loss_map_quantile_value
        CHECK(
            ((statistics = 'quantile') AND (quantile IS NOT NULL))
            OR (((statistics != 'quantile') AND (quantile IS NULL))))
) TABLESPACE riskr_ts;

CREATE TABLE riskr.loss_map_data (
    id SERIAL PRIMARY KEY,
    loss_map_id INTEGER NOT NULL, -- FK to loss_map.id
    asset_ref VARCHAR NOT NULL,
    -- for scenario calculations value correspond to a mean value
    value float NOT NULL,
    -- for non-scenario calculations std_dev is NULL
    std_dev float NULL
) TABLESPACE riskr_ts;
SELECT AddGeometryColumn('riskr', 'loss_map_data', 'location', 4326, 'POINT', 2);
ALTER TABLE riskr.loss_map_data ALTER COLUMN location SET NOT NULL;


-- Loss fraction data.
CREATE TABLE riskr.loss_fraction (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    hazard_output_id INTEGER NULL,
    variable VARCHAR NOT NULL,
    statistics VARCHAR CONSTRAINT loss_fraction_statistics
        CHECK(statistics IS NULL OR
              statistics IN ('mean', 'quantile')),
    -- Quantile value (only for "quantile" statistics)
    quantile float CONSTRAINT loss_fraction_quantile_value
        CHECK(
            ((statistics = 'quantile') AND (quantile IS NOT NULL))
            OR (((statistics != 'quantile') AND (quantile IS NULL)))),
    -- poe is significant only for classical calculations
    poe FLOAT NULL CONSTRAINT valid_poe
        CHECK (poe IS NULL OR (poe >= 0.0) AND (poe <= 1.0))
) TABLESPACE riskr_ts;

CREATE TABLE riskr.loss_fraction_data (
    id SERIAL PRIMARY KEY,
    loss_fraction_id INTEGER NOT NULL, -- FK to loss_fraction.id
    --- Holds a serialized representation of `variable`. if `variable`
    --- is a taxonomy, then `value` is a string representing an asset
    --- taxonomy
    value VARCHAR NOT NULL,
    absolute_loss FLOAT NOT NULL
) TABLESPACE riskr_ts;
SELECT AddGeometryColumn('riskr', 'loss_fraction_data', 'location', 4326, 'POINT', 2);
ALTER TABLE riskr.loss_fraction_data ALTER COLUMN location SET NOT NULL;


-- Aggregate Loss.
CREATE TABLE riskr.aggregate_loss (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    insured BOOLEAN NOT NULL DEFAULT false,
    mean float NOT NULL,
    std_dev float NULL
) TABLESPACE riskr_ts;


-- Event Loss table.
CREATE TABLE riskr.event_loss (
    id SERIAL PRIMARY KEY,

    -- FK to uiapi.output.id. The corresponding row must have
    -- output_type == event_loss
    output_id INTEGER NOT NULL,
    rupture_id INTEGER NOT NULL, -- FK to hzrdr.ses_rupture.id
    aggregate_loss float NOT NULL
) TABLESPACE riskr_ts;


-- Loss curve.
CREATE TABLE riskr.loss_curve (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    hazard_output_id INTEGER NULL,
    aggregate BOOLEAN NOT NULL DEFAULT false,
    insured BOOLEAN NOT NULL DEFAULT false,

    statistics VARCHAR CONSTRAINT loss_curve_statistics
        CHECK(statistics IS NULL OR
              statistics IN ('mean', 'quantile')),
    -- Quantile value (only for "quantile" statistics)
    quantile float CONSTRAINT loss_curve_quantile_value
        CHECK(
            ((statistics = 'quantile') AND (quantile IS NOT NULL))
            OR (((statistics != 'quantile') AND (quantile IS NULL))))
) TABLESPACE riskr_ts;


-- Loss curve data. Holds the asset, its position and value plus the calculated
-- curve.
CREATE TABLE riskr.loss_curve_data (
    id SERIAL PRIMARY KEY,
    loss_curve_id INTEGER NOT NULL,

    asset_ref VARCHAR NOT NULL,
    -- needed to compute absolute losses in the export phase
    asset_value float NOT NULL,
    loss_ratios float[] NOT NULL,
    -- Probabilities of exceedence
    poes float[] NOT NULL,

    -- Average Loss ratio
    average_loss_ratio FLOAT NOT NULL
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
    poes float[] NOT NULL,

    -- Absolute Loss
    average_loss FLOAT NOT NULL
) TABLESPACE riskr_ts;

-- Benefit-cost ratio distribution
CREATE TABLE riskr.bcr_distribution (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    hazard_output_id INTEGER NULL
) TABLESPACE riskr_ts;

CREATE TABLE riskr.bcr_distribution_data (
    id SERIAL PRIMARY KEY,
    bcr_distribution_id INTEGER NOT NULL, -- FK to bcr_distribution.id
    asset_ref VARCHAR NOT NULL,
    average_annual_loss_original float NOT NULL,
    average_annual_loss_retrofitted float NOT NULL,
    bcr float NOT NULL
) TABLESPACE riskr_ts;
SELECT AddGeometryColumn('riskr', 'bcr_distribution_data', 'location', 4326, 'POINT', 2);
ALTER TABLE riskr.bcr_distribution_data ALTER COLUMN location SET NOT NULL;

CREATE TABLE riskr.dmg_state (
    id SERIAL PRIMARY KEY,
    risk_calculation_id INTEGER NOT NULL REFERENCES uiapi.risk_calculation,
    dmg_state VARCHAR NOT NULL,
    lsi SMALLINT NOT NULL CHECK(lsi >= 0),
    UNIQUE (risk_calculation_id, dmg_state),
    UNIQUE (risk_calculation_id, lsi));

-- Damage Distribution Per Asset
CREATE TABLE riskr.dmg_dist_per_asset (
    id SERIAL PRIMARY KEY,
    dmg_state_id INTEGER NOT NULL REFERENCES riskr.dmg_state,
    exposure_data_id INTEGER NOT NULL,  -- FK to oqmif.exposure_data.id
    mean float NOT NULL,
    stddev float NOT NULL
) TABLESPACE riskr_ts;


-- Damage Distrubtion Per Taxonomy
CREATE TABLE riskr.dmg_dist_per_taxonomy (
    id SERIAL PRIMARY KEY,
    dmg_state_id INTEGER NOT NULL REFERENCES riskr.dmg_state,
    taxonomy VARCHAR NOT NULL,
    mean float NOT NULL,
    stddev float NOT NULL
) TABLESPACE riskr_ts;


-- Total Damage Distribution
CREATE TABLE riskr.dmg_dist_total (
    id SERIAL PRIMARY KEY,
    dmg_state_id INTEGER NOT NULL REFERENCES riskr.dmg_state,
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

    site GEOGRAPHY(point) NOT NULL,

    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL,
    UNIQUE (exposure_model_id, asset_ref)
) TABLESPACE oqmif_ts;


CREATE TABLE oqmif.occupancy (
    id SERIAL PRIMARY KEY,
    exposure_data_id INTEGER NOT NULL,
    description VARCHAR NOT NULL,
    occupants INTEGER NOT NULL
) TABLESPACE oqmif_ts;

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

-- pre-computed calculation point of interest to site parameters table
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

ALTER TABLE hzrdi.parsed_rupture_model ADD CONSTRAINT hzrdi_parsed_rupture_model_input_fk
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
ON DELETE CASCADE;

ALTER TABLE uiapi.oq_job ADD CONSTRAINT uiapi_oq_job_risk_calculation
FOREIGN KEY (risk_calculation_id) REFERENCES uiapi.risk_calculation(id)
ON DELETE CASCADE;

ALTER TABLE uiapi.hazard_calculation ADD CONSTRAINT uiapi_hazard_calculation_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.input2hcalc ADD CONSTRAINT uiapi_input2hcalc_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.input2hcalc ADD CONSTRAINT uiapi_input2hcalc_hazard_calculation_fk
FOREIGN KEY (hazard_calculation_id) REFERENCES uiapi.hazard_calculation(id) ON DELETE CASCADE;

ALTER TABLE uiapi.risk_calculation ADD CONSTRAINT uiapi_risk_calculation_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.risk_calculation ADD CONSTRAINT uiapi_risk_calculation_hazard_output_fk
FOREIGN KEY (hazard_output_id) REFERENCES uiapi.output(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.risk_calculation ADD CONSTRAINT uiapi_risk_calculation_input_fk
FOREIGN KEY (exposure_input_id) REFERENCES uiapi.input(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.input2rcalc ADD CONSTRAINT uiapi_input2rcalc_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.input2rcalc ADD CONSTRAINT uiapi_input2rcalc_risk_calculation_fk
FOREIGN KEY (risk_calculation_id) REFERENCES uiapi.risk_calculation(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.oq_job_profile ADD CONSTRAINT uiapi_oq_job_profile_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.performance ADD CONSTRAINT uiapi_performance_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

ALTER TABLE uiapi.job_stats ADD CONSTRAINT uiapi_job_stats_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

ALTER TABLE uiapi.job_phase_stats ADD CONSTRAINT  uiapi_job_phase_stats_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

ALTER TABLE uiapi.cnode_stats ADD CONSTRAINT  uiapi_cnode_stats_oq_job_fk
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

ALTER TABLE uiapi.input ADD CONSTRAINT uiapi_input_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.input ADD CONSTRAINT uiapi_input_model_content_fk
FOREIGN KEY (model_content_id) REFERENCES uiapi.model_content(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.output ADD CONSTRAINT uiapi_output_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

ALTER TABLE uiapi.output ADD CONSTRAINT uiapi_output_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.error_msg ADD CONSTRAINT uiapi_error_msg_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

ALTER TABLE oqmif.exposure_model ADD CONSTRAINT oqmif_exposure_model_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE oqmif.exposure_model ADD CONSTRAINT oqmif_exposure_model_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE RESTRICT;

ALTER TABLE hzrdr.hazard_map
ADD CONSTRAINT hzrdr_hazard_map_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE hzrdr.hazard_map
ADD CONSTRAINT hzrdr_hazard_map_lt_realization_fk
FOREIGN KEY (lt_realization_id) REFERENCES hzrdr.lt_realization(id)
ON DELETE CASCADE;

ALTER TABLE hzrdr.hazard_curve
ADD CONSTRAINT hzrdr_hazard_curve_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE hzrdr.hazard_curve
ADD CONSTRAINT hzrdr_hazard_curve_lt_realization_fk
FOREIGN KEY (lt_realization_id) REFERENCES hzrdr.lt_realization(id)
ON DELETE CASCADE;

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
ON DELETE CASCADE;

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

-- gmf_scenario -> output FK
ALTER TABLE hzrdr.gmf_scenario
ADD CONSTRAINT hzrdr_gmf_scenario_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id)
ON DELETE CASCADE;

-- disagg_result -> output FK
ALTER TABLE hzrdr.disagg_result
ADD CONSTRAINT hzrdr_disagg_result_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id)
ON DELETE CASCADE;

-- disagg_result -> lt_realization FK
ALTER TABLE hzrdr.disagg_result
ADD CONSTRAINT hzrdr_disagg_result_lt_realization_fk
FOREIGN KEY (lt_realization_id) REFERENCES hzrdr.lt_realization(id)
ON DELETE CASCADE;


-- UHS:
-- uhs -> output FK
ALTER TABLE hzrdr.uhs
ADD CONSTRAINT hzrdr_uhs_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

-- uhs -> hzrdr.lt_realization FK
ALTER TABLE hzrdr.uhs
ADD CONSTRAINT hzrdr_uhs_lt_realization_fk
FOREIGN KEY (lt_realization_id) REFERENCES hzrdr.lt_realization(id)
ON DELETE CASCADE;

-- uhs_data -> uhs FK
ALTER TABLE hzrdr.uhs_data
ADD CONSTRAINT hzrdr_uhs_data_uhs_fk
FOREIGN KEY (uhs_id) REFERENCES hzrdr.uhs(id) ON DELETE CASCADE;

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
ON DELETE CASCADE;

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

ALTER TABLE riskr.loss_map
ADD CONSTRAINT riskr_loss_map_hazard_output_fk
FOREIGN KEY (hazard_output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.loss_map_data
ADD CONSTRAINT riskr_loss_map_data_loss_map_fk
FOREIGN KEY (loss_map_id) REFERENCES riskr.loss_map(id) ON DELETE CASCADE;

ALTER TABLE riskr.loss_fraction
ADD CONSTRAINT riskr_loss_fraction_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.loss_fraction
ADD CONSTRAINT riskr_loss_fraction_hazard_output_fk
FOREIGN KEY (hazard_output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.loss_fraction_data
ADD CONSTRAINT riskr_loss_fraction_data_loss_map_fk
FOREIGN KEY (loss_fraction_id) REFERENCES riskr.loss_fraction(id) ON DELETE CASCADE;

ALTER TABLE riskr.loss_curve
ADD CONSTRAINT riskr_loss_curve_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.loss_curve
ADD CONSTRAINT riskr_loss_curve_hazard_output_fk
FOREIGN KEY (hazard_output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.bcr_distribution
ADD CONSTRAINT riskr_bcr_distribution_hazard_output_fk
FOREIGN KEY (hazard_output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.loss_curve_data
ADD CONSTRAINT riskr_loss_curve_data_loss_curve_fk
FOREIGN KEY (loss_curve_id) REFERENCES riskr.loss_curve(id) ON DELETE CASCADE;

ALTER TABLE riskr.aggregate_loss_curve_data
ADD CONSTRAINT riskr_aggregate_loss_curve_data_loss_curve_fk
FOREIGN KEY (loss_curve_id) REFERENCES riskr.loss_curve(id) ON DELETE CASCADE;

ALTER TABLE riskr.aggregate_loss
ADD CONSTRAINT riskr_aggregate_loss_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.event_loss
ADD CONSTRAINT riskr_event_loss_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.event_loss
ADD CONSTRAINT riskr_evet_loss_sesrupture_fk
FOREIGN KEY (rupture_id) REFERENCES hzrdr.ses_rupture(id) ON DELETE CASCADE;

ALTER TABLE riskr.bcr_distribution_data
ADD CONSTRAINT riskr_bcr_distribution_data_bcr_distribution_fk
FOREIGN KEY (bcr_distribution_id) REFERENCES riskr.bcr_distribution(id) ON DELETE CASCADE;


-- Damage Distribution, Per Asset

ALTER TABLE riskr.dmg_dist_per_asset
ADD CONSTRAINT riskr_dmg_dist_per_asset_exposure_data_fk
FOREIGN KEY (exposure_data_id) REFERENCES oqmif.exposure_data(id) ON DELETE RESTRICT;


ALTER TABLE oqmif.exposure_data ADD CONSTRAINT
oqmif_exposure_data_exposure_model_fk FOREIGN KEY (exposure_model_id)
REFERENCES oqmif.exposure_model(id) ON DELETE CASCADE;

ALTER TABLE oqmif.occupancy ADD CONSTRAINT
oqmif_occupancy_exposure_data_fk FOREIGN KEY (exposure_data_id)
REFERENCES oqmif.exposure_data(id) ON DELETE CASCADE;

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

---------------------- views ----------------------------

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


-- convenience view to analyze the performance of the jobs;
-- for instance the slowest operations can be extracted with 
-- SELECT DISTINCT ON (oq_job_id) * FROM uiapi.performance_view;
CREATE VIEW uiapi.performance_view AS
SELECT h.id AS hazard_calculation_id, description, p.* FROM (
     SELECT oq_job_id, operation, sum(duration) AS duration,
     max(pymemory) AS pymemory, max(pgmemory) AS pgmemory, count(*) AS counts
     FROM uiapi.performance
     GROUP BY oq_job_id, operation ORDER BY oq_job_id, duration DESC) AS p
INNER JOIN uiapi.oq_job AS o
ON p.oq_job_id=o.id
INNER JOIN uiapi.hazard_calculation AS h
ON h.id=o.hazard_calculation_id;
