/*
  Copyright (C) 2010-2016, GEM Foundation.

  OpenQuake is free software: you can redistribute it and/or modify it
  under the terms of the GNU Affero General Public License as published
  by the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  OpenQuake is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU Affero General Public License
  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
*/


-- Disable unnecessarily verbose output
SET client_min_messages TO WARNING;

-- Set role to oq_admin
SET ROLE TO oq_admin;

------------------------------------------------------------------------
-- Name space definitions go here
------------------------------------------------------------------------
CREATE SCHEMA hzrdi;
CREATE SCHEMA hzrdr;
CREATE SCHEMA riski;
CREATE SCHEMA riskr;
CREATE SCHEMA uiapi;
COMMENT ON SCHEMA hzrdi IS 'Hazard input model';
COMMENT ON SCHEMA hzrdr IS 'Hazard result data';
COMMENT ON SCHEMA riski IS 'Risk input model';
COMMENT ON SCHEMA riskr IS 'Risk result data';
COMMENT ON SCHEMA uiapi IS 'Data required by the API presented to the various OpenQuake UIs';

------------------------------------------------------------------------
-- Table definitions go here
------------------------------------------------------------------------


-- Site-specific parameters for hazard calculations.
CREATE TABLE hzrdi.site_model (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL,
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

-- table for the intensity measure types
CREATE TABLE hzrdi.imt(
  id SERIAL PRIMARY KEY,
  imt_str VARCHAR UNIQUE NOT NULL, -- full string representation of the IMT
  im_type VARCHAR NOT NULL, -- short string for the IMT
  sa_period FLOAT CONSTRAINT imt_sa_period
        CHECK(((im_type = 'SA') AND (sa_period IS NOT NULL))
              OR ((im_type != 'SA') AND (sa_period IS NULL))),
  sa_damping FLOAT CONSTRAINT imt_sa_damping
        CHECK(((im_type = 'SA') AND (sa_damping IS NOT NULL))
            OR ((im_type != 'SA') AND (sa_damping IS NULL))),
  UNIQUE (im_type, sa_period, sa_damping)
) TABLESPACE hzrdi_ts;

-- An OpenQuake engine run started by the user
CREATE TABLE uiapi.oq_job (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR NOT NULL,
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
    risklib_version VARCHAR,
    is_running BOOLEAN NOT NULL DEFAULT FALSE,
    duration INTEGER NOT NULL DEFAULT 0,
    job_pid INTEGER NOT NULL DEFAULT 0,
    supervisor_pid INTEGER NOT NULL DEFAULT 0,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;

COMMENT ON TABLE uiapi.oq_job IS 'Date related to an OpenQuake job that was created in the UI.';
COMMENT ON COLUMN uiapi.oq_job.job_pid IS 'The process id (PID) of the OpenQuake engine runner process';
COMMENT ON COLUMN uiapi.oq_job.supervisor_pid IS 'The process id (PID) of the supervisor for this OpenQuake job';
COMMENT ON COLUMN uiapi.oq_job.status IS 'One of: pending, running, failed or succeeded.';
COMMENT ON COLUMN uiapi.oq_job.duration IS 'The job''s duration in seconds (only available once the jobs terminates).';

-- Tracks task performance
CREATE TABLE uiapi.performance (
    id SERIAL PRIMARY KEY,
    oq_job_id INTEGER NOT NULL,
    task_id VARCHAR,
    start_time timestamp without time zone NOT NULL,
    task VARCHAR,
    operation VARCHAR NOT NULL,
    duration FLOAT,
    pymemory BIGINT,
    pgmemory BIGINT
)  TABLESPACE uiapi_ts;

COMMENT ON TABLE uiapi.performance IS 'Tracks task performance';
COMMENT ON COLUMN uiapi.performance.duration IS 'Duration of the operation in seconds';
COMMENT ON COLUMN uiapi.performance.pymemory IS 'Memory occupation in Python (Mbytes)';
COMMENT ON COLUMN uiapi.performance.pgmemory IS 'Memory occupation in Postgres (Mbytes)';


-- Tracks various job statistics
CREATE TABLE uiapi.job_stats (
    id SERIAL PRIMARY KEY,
    oq_job_id INTEGER NOT NULL,
    start_time timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL,
    stop_time timestamp without time zone,
    -- The number of total sites in the calculation
    disk_space BIGINT -- The disk space occupation in bytes
) TABLESPACE uiapi_ts;

COMMENT ON TABLE uiapi.job_stats IS 'Tracks various job statistics';
COMMENT ON COLUMN uiapi.job_stats.disk_space IS 'How much the disk space occupation increased during the computation (in bytes)';


CREATE TABLE uiapi.hazard_calculation (
    id SERIAL PRIMARY KEY,
    -- Contains the absolute path to the directory containing the job config
    -- file
    base_path VARCHAR NOT NULL,
    export_dir VARCHAR,
    -- general parameters:
    -- (see also `region` and `sites` geometries defined below)
    description VARCHAR NOT NULL DEFAULT '',
    calculation_mode VARCHAR NOT NULL CONSTRAINT haz_calc_mode
        CHECK(calculation_mode IN (
            'classical',
            'event_based',
            'disaggregation',
            'scenario'
        )),
    inputs BYTEA,  -- stored as a pickled Python `dict`
    region_grid_spacing float,
    -- logic tree parameters:
    random_seed INTEGER NOT NULL,
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
    ground_motion_fields BOOLEAN,
    hazard_curves_from_gmfs BOOLEAN
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'hazard_calculation', 'region', 4326, 'POLYGON', 2);
SELECT AddGeometryColumn('uiapi', 'hazard_calculation', 'sites', 4326, 'MULTIPOINT', 2);


CREATE TABLE uiapi.risk_calculation (
    id SERIAL PRIMARY KEY,
    -- Contains the absolute path to the directory containing the job config
    -- file
    base_path VARCHAR NOT NULL,
    export_dir VARCHAR,
    -- general parameters:
    description VARCHAR NOT NULL DEFAULT '',
    calculation_mode VARCHAR NOT NULL,
    inputs BYTEA,  -- stored as a pickled Python `dict`

    maximum_distance FLOAT NULL,

    preloaded_exposure_model_id INTEGER,

    hazard_output_id INTEGER NULL,  -- FK to uiapi.output
    hazard_calculation_id INTEGER NULL,  -- FK to uiapi.hazard_calculation

    risk_investigation_time float NULL,

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
    master_seed INTEGER NOT NULL,

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
    asset_life_expectancy float,

    -- Scenario parameters:
    time_event VARCHAR
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'risk_calculation', 'region_constraint', 4326, 'POLYGON', 2);
SELECT AddGeometryColumn('uiapi', 'risk_calculation', 'sites_disagg', 4326, 'MULTIPOINT', 2);

-- A single OpenQuake calculation engine output. The data may reside in a file
-- or in the database.
CREATE TABLE uiapi.output (
    id SERIAL PRIMARY KEY,
    oq_job_id INTEGER NOT NULL,
    -- The full path of the output file on the server, optional and only set
    -- for outputs with NRML/XML files.
    display_name VARCHAR NOT NULL,
    output_type VARCHAR NOT NULL CONSTRAINT output_type_value
        CHECK(output_type IN (
            'agg_loss_curve',
            'aggregate_loss',
            'bcr_distribution',
            'collapse_map',
            'disagg_matrix',
            'dmg_dist_per_asset',
            'dmg_dist_per_taxonomy',
            'dmg_dist_total',
            'event_loss',
            'event_loss_curve',
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

COMMENT ON TABLE uiapi.output IS 'A single OpenQuake calculation engine output. The data may reside in a file or in the database.';
COMMENT ON COLUMN uiapi.output.display_name IS 'The GUI display name to be used for this output.';
COMMENT ON COLUMN uiapi.output.output_type IS 'Output type, one of:
    - unknown
    - hazard_curve
    - hazard_map
    - gmf
    - loss_curve
    - loss_map
    - dmg_dist_per_asset
    - dmg_dist_per_taxonomy
    - dmg_dist_total
    - bcr_distribution';
COMMENT ON COLUMN uiapi.output.oq_job_id IS 'The job that produced this output;
NULL if the output was imported from an external source';


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
    lons float[] NOT NULL,
    lats float[] NOT NULL,
    imls float[] NOT NULL
) TABLESPACE hzrdr_ts;

COMMENT ON TABLE hzrdr.hazard_map IS 'A complete hazard map, for a given IMT and PoE';
COMMENT ON COLUMN hzrdr.hazard_map.poe IS 'Probability of exceedence';
COMMENT ON COLUMN hzrdr.hazard_map.statistics IS 'Statistic type, one of:
    - Median   (median)
    - Quantile (quantile)';
COMMENT ON COLUMN hzrdr.hazard_map.quantile IS 'The quantile level for quantile statistical data.';


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

COMMENT ON TABLE hzrdr.hazard_curve IS 'A collection of hazard curves. This table defines common attributes for the collection.';
COMMENT ON COLUMN hzrdr.hazard_curve.output_id IS 'The foreign key to the output record that represents the corresponding hazard curve.';
COMMENT ON COLUMN hzrdr.hazard_curve.lt_realization_id IS 'Only required for non-statistical curves';
COMMENT ON COLUMN hzrdr.hazard_curve.imt IS 'Intensity Measure Type: PGA, PGV, PGD, SA, IA, RSD, or MMI';
COMMENT ON COLUMN hzrdr.hazard_curve.imls IS 'Intensity Measure Levels common to this set of hazard curves';
COMMENT ON COLUMN hzrdr.hazard_curve.statistics IS 'Statistic type, one of:
    - Mean     (mean)
    - Quantile (quantile)';
COMMENT ON COLUMN hzrdr.hazard_curve.quantile IS 'The quantile for quantile statistical data.';
COMMENT ON COLUMN hzrdr.hazard_curve.sa_period IS 'Spectral Acceleration period; only relevent when imt = SA';
COMMENT ON COLUMN hzrdr.hazard_curve.sa_damping IS 'Spectral Acceleration damping; only relevent when imt = SA';


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

COMMENT ON TABLE hzrdr.hazard_curve_data IS 'Holds location/POE data for hazard curves';
COMMENT ON COLUMN hzrdr.hazard_curve_data.hazard_curve_id IS 'The foreign key to the hazard curve record for this node.';
COMMENT ON COLUMN hzrdr.hazard_curve_data.poes IS 'Probabilities of exceedence.';

-- Stochastic Event Set Collection
-- A container for all of the Stochastic Event Sets in a given
-- logic tree realization.
CREATE TABLE hzrdr.ses_collection (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    lt_model_id INTEGER, -- can be null for scenario
    ordinal INTEGER NOT NULL
) TABLESPACE hzrdr_ts;

-- A rupture as part of a Stochastic Event Set Collection.
-- Ruptures will have different geometrical definitions, depending on whether
-- the event was generated from a point/area source or a simple/complex fault
-- source.
CREATE TABLE hzrdr.probabilistic_rupture (
    id SERIAL PRIMARY KEY,
    ses_collection_id INTEGER NOT NULL,
    rake float NOT NULL,
    is_from_fault_source BOOLEAN NOT NULL,
    is_multi_surface BOOLEAN NOT NULL,
    surface BYTEA NOT NULL,
    magnitude float NOT NULL,
    _hypocenter FLOAT[3],
    site_indices INTEGER[],
    trt_model_id INTEGER NOT NULL
) TABLESPACE hzrdr_ts;


CREATE TABLE hzrdr.ses_rupture (
    id SERIAL PRIMARY KEY,
    ses_id INTEGER NOT NULL,
    rupture_id INTEGER NOT NULL,  -- FK to probabilistic_rupture.id
    tag VARCHAR NOT NULL,
    seed INTEGER NOT NULL
) TABLESPACE hzrdr_ts;

-- gmf_rupture table ---------------------------------------------------
CREATE TABLE hzrdr.gmf_rupture (
   id SERIAL PRIMARY KEY,
   rupture_id INTEGER NOT NULL,  -- fk to hzrdr.ses_rupture
   gsim TEXT NOT NULL,
   imt TEXT NOT NULL, -- fk to hzrdi.imt
   ground_motion_field FLOAT[] NOT NULL
) TABLESPACE hzrdr_ts;

CREATE TABLE hzrdr.gmf (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,  -- FK to output.id
    -- FK to lt_realization.id
    lt_realization_id INTEGER  -- can be NULL for scenario calculator
) TABLESPACE hzrdr_ts;

CREATE TABLE hzrdr.gmf_data (
    id SERIAL PRIMARY KEY,
    gmf_id INTEGER NOT NULL, -- fk -> gmf
    task_no INTEGER NOT NULL,
    imt VARCHAR NOT NULL,
        CONSTRAINT hazard_curve_imt
        CHECK(imt in ('PGA', 'PGV', 'PGD', 'SA', 'IA', 'RSD', 'MMI')),
    sa_period float,
        CONSTRAINT gmf_sa_period
        CHECK(
            ((imt = 'SA') AND (sa_period IS NOT NULL))
            OR ((imt != 'SA') AND (sa_period IS NULL))),
    sa_damping float,
        CONSTRAINT gmf_sa_damping
        CHECK(
            ((imt = 'SA') AND (sa_damping IS NOT NULL))
            OR ((imt != 'SA') AND (sa_damping IS NULL))),
    gmvs float[] NOT NULL,
    rupture_ids int[],
    site_id INTEGER NOT NULL -- fk -> hazard_site
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

-- logic tree source models
CREATE TABLE hzrdr.lt_source_model (
   id SERIAL PRIMARY KEY,
   hazard_calculation_id INTEGER NOT NULL,
   ordinal INTEGER NOT NULL,
    -- A list of the logic tree branchIDs
   sm_lt_path VARCHAR[] NOT NULL,
   sm_name VARCHAR NOT NULL,
   weight NUMERIC
) TABLESPACE hzrdr_ts;

-- logic tree source model infos
CREATE TABLE hzrdr.trt_model (
   id SERIAL PRIMARY KEY,
   lt_model_id INTEGER, -- fk to lt_source_model
   tectonic_region_type TEXT NOT NULL,
   num_sources INTEGER NOT NULL,
   num_ruptures INTEGER NOT NULL,
   min_mag FLOAT NOT NULL,
   max_mag FLOAT NOT NULL,
   gsims TEXT[]
) TABLESPACE hzrdr_ts;

-- specific source info
CREATE TABLE hzrdr.source_info (
  id SERIAL,
  trt_model_id INTEGER NOT NULL,
  source_id TEXT NOT NULL,
  source_class TEXT NOT NULL,
  num_sites INTEGER NOT NULL,
  num_ruptures INTEGER NOT NULL,
  occ_ruptures INTEGER NOT NULL,
  calc_time FLOAT NOT NULL
) TABLESPACE hzrdr_ts;

-- associations logic tree realizations <-> trt_models
CREATE TABLE hzrdr.assoc_lt_rlz_trt_model(
id SERIAL,
rlz_id INTEGER NOT NULL,
trt_model_id INTEGER NOT NULL,
gsim TEXT NOT NULL
) TABLESPACE hzrdr_ts;

-- keep track of logic tree realization progress for a given calculation
CREATE TABLE hzrdr.lt_realization (
    id SERIAL PRIMARY KEY,
    lt_model_id INTEGER NOT NULL, -- fk hzrdr.lt_mode.id
    ordinal INTEGER NOT NULL,
    weight NUMERIC, -- path weight
    gsim_lt_path VARCHAR[] NOT NULL -- list of the logic tree branchIDs
) TABLESPACE hzrdr_ts;


-- Loss map data.
CREATE TABLE riskr.loss_map (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    loss_type VARCHAR NOT NULL,
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

COMMENT ON TABLE riskr.loss_map IS 'Holds metadata for loss maps.';
COMMENT ON COLUMN riskr.loss_map.output_id IS 'The foreign key to the output record that represents the corresponding loss map.';
COMMENT ON COLUMN riskr.loss_map.poe IS 'Probability of exceedance (for probabilistic loss maps)';


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

COMMENT ON TABLE riskr.loss_map_data IS 'Holds an asset, its position and a value plus (for non-scenario maps) the standard deviation for its loss.';
COMMENT ON COLUMN riskr.loss_map_data.loss_map_id IS 'The foreign key to the loss map';
COMMENT ON COLUMN riskr.loss_map_data.asset_ref IS 'The asset reference';
COMMENT ON COLUMN riskr.loss_map_data.location IS 'The position of the asset';
COMMENT ON COLUMN riskr.loss_map_data.value IS 'The value of the loss';
COMMENT ON COLUMN riskr.loss_map_data.std_dev IS 'The standard deviation of the loss (for scenario maps, for non-scenario maps the standard deviation is NULL)';


-- Loss fraction data.
CREATE TABLE riskr.loss_fraction (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    loss_type VARCHAR NOT NULL,
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
    loss_type VARCHAR NOT NULL,
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
    hazard_output_id INTEGER NULL,
    loss_type VARCHAR NOT NULL
) TABLESPACE riskr_ts;


-- Event Loss table.
CREATE TABLE riskr.event_loss_data (
    id SERIAL PRIMARY KEY,

    event_loss_id INTEGER NOT NULL,
    rupture_id INTEGER NOT NULL, -- FK to hzrdr.ses_rupture.id
    aggregate_loss float NOT NULL
) TABLESPACE riskr_ts;


-- Loss curve.
CREATE TABLE riskr.loss_curve (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    loss_type VARCHAR NOT NULL,
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

COMMENT ON TABLE riskr.loss_curve IS 'Holds the parameters common to a set of loss curves.';
COMMENT ON COLUMN riskr.loss_curve.output_id IS 'The foreign key to the output record that represents the corresponding loss curve.';
COMMENT ON COLUMN riskr.loss_curve.aggregate IS 'Is the curve an aggregate curve?';

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
    average_loss_ratio FLOAT NOT NULL,

    -- Average Loss ratio
    stddev_loss_ratio FLOAT
) TABLESPACE riskr_ts;
SELECT AddGeometryColumn('riskr', 'loss_curve_data', 'location', 4326, 'POINT',
                         2);
ALTER TABLE riskr.loss_curve_data ALTER COLUMN location SET NOT NULL;

COMMENT ON TABLE riskr.loss_curve_data IS 'Holds the probabilities of exceedance for a given loss curve.';
COMMENT ON COLUMN riskr.loss_curve_data.loss_curve_id IS 'The foreign key to the curve record to which the loss curve data belongs';
COMMENT ON COLUMN riskr.loss_curve_data.asset_ref IS 'The asset id';
COMMENT ON COLUMN riskr.loss_curve_data.location IS 'The position of the asset';
COMMENT ON COLUMN riskr.loss_curve_data.asset_value IS 'The value of the asset';
COMMENT ON COLUMN riskr.loss_curve_data.loss_ratios IS 'Loss ratios';
COMMENT ON COLUMN riskr.loss_curve_data.poes IS 'Probabilities of exceedence';


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
    average_loss FLOAT NOT NULL,

    -- StdDev of losses
    stddev_loss FLOAT
) TABLESPACE riskr_ts;

COMMENT ON TABLE riskr.aggregate_loss_curve_data IS 'Holds the probabilities of exceedance for the whole exposure model.';
COMMENT ON COLUMN riskr.aggregate_loss_curve_data.loss_curve_id IS 'The foreign key to the loss curve record to which the aggregate loss curve data belongs';
COMMENT ON COLUMN riskr.aggregate_loss_curve_data.losses IS 'Losses';
COMMENT ON COLUMN riskr.aggregate_loss_curve_data.poes IS 'Probabilities of exceedence';

-- Benefit-cost ratio distribution
CREATE TABLE riskr.bcr_distribution (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    loss_type VARCHAR NOT NULL,
    hazard_output_id INTEGER NULL
) TABLESPACE riskr_ts;

COMMENT ON TABLE riskr.bcr_distribution IS 'Holds metadata for the benefit-cost ratio distribution';
COMMENT ON COLUMN riskr.bcr_distribution.output_id IS 'The foreign key to the output record that represents the corresponding BCR distribution.';


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

COMMENT ON TABLE riskr.bcr_distribution_data IS 'Holds the actual data for the BCR distribution';
COMMENT ON COLUMN riskr.bcr_distribution_data.bcr_distribution_id IS 'The foreign key to the record to which the BCR distribution data belongs';
COMMENT ON COLUMN riskr.bcr_distribution_data.asset_ref IS 'The asset id';
COMMENT ON COLUMN riskr.bcr_distribution_data.average_annual_loss_original IS 'The Expected annual loss computed by using the original model';
COMMENT ON COLUMN riskr.bcr_distribution_data.average_annual_loss_retrofitted IS 'The Expected annual loss computed by using the retrofitted model';
COMMENT ON COLUMN riskr.bcr_distribution_data.bcr IS 'The actual benefit-cost ratio';


CREATE TABLE riskr.dmg_state (
    id SERIAL PRIMARY KEY,
    risk_calculation_id INTEGER NOT NULL REFERENCES uiapi.risk_calculation,
    dmg_state VARCHAR NOT NULL,
    lsi SMALLINT NOT NULL CHECK(lsi >= 0),
    UNIQUE (risk_calculation_id, dmg_state),
    UNIQUE (risk_calculation_id, lsi)
) TABLESPACE riskr_ts;

COMMENT ON TABLE riskr.dmg_state IS 'Holds the damage_states associated to a given output';


-- Damage Distribution Per Asset
CREATE TABLE riskr.dmg_dist_per_asset (
    id SERIAL PRIMARY KEY,
    dmg_state_id INTEGER NOT NULL REFERENCES riskr.dmg_state,
    exposure_data_id INTEGER NOT NULL,  -- FK to riski.exposure_data.id
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
CREATE TABLE riski.exposure_model (
    id SERIAL PRIMARY KEY,
    -- Associates the risk exposure model with an input record
    job_id INTEGER NOT NULL,
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

    deductible_absolute BOOLEAN DEFAULT TRUE,
    insurance_limit_absolute BOOLEAN DEFAULT TRUE

) TABLESPACE riski_ts;

COMMENT ON TABLE riski.exposure_model IS 'A risk exposure model';
COMMENT ON COLUMN riski.exposure_model.area_type IS 'area type. one of: aggregated or per_asset';
COMMENT ON COLUMN riski.exposure_model.area_unit IS 'area unit of measure e.g. sqm';
COMMENT ON COLUMN riski.exposure_model.category IS 'The risk category modelled';
COMMENT ON COLUMN riski.exposure_model.description IS 'An optional description of the risk exposure model at hand';

COMMENT ON COLUMN riski.exposure_model.name IS 'The exposure model name';

COMMENT ON COLUMN riski.exposure_model.taxonomy_source IS 'the taxonomy system used to classify the assets';


-- Cost Conversion table
CREATE TABLE riski.cost_type (
    id SERIAL PRIMARY KEY,
    exposure_model_id INTEGER NOT NULL,

    name VARCHAR NOT NULL,
    conversion VARCHAR NOT NULL CONSTRAINT conversion_value
        CHECK(conversion = 'per_asset'
              OR conversion = 'per_area'
              OR conversion = 'aggregated'),
    unit VARCHAR,
    retrofitted_conversion VARCHAR CONSTRAINT retrofitted_conversion_value
        CHECK(retrofitted_conversion IS NULL
              OR retrofitted_conversion = 'per_asset'
              OR retrofitted_conversion = 'per_area'
              OR retrofitted_conversion = 'aggregated'),
    retrofitted_unit VARCHAR
) TABLESPACE riski_ts;


-- Per-asset exposure data
CREATE TABLE riski.exposure_data (
    id SERIAL PRIMARY KEY,
    exposure_model_id INTEGER NOT NULL,
    -- the asset reference is unique within an exposure model.
    asset_ref VARCHAR NOT NULL,

    -- vulnerability function reference
    taxonomy VARCHAR NOT NULL,

    -- number of assets, people etc.
    number_of_units float CONSTRAINT units_value CHECK(number_of_units >= 0.0),
    area float CONSTRAINT area_value CHECK(area >= 0.0),

    site GEOGRAPHY(point) NOT NULL,
    UNIQUE (exposure_model_id, asset_ref)
) TABLESPACE riski_ts;

COMMENT ON TABLE riski.exposure_data IS 'Per-asset risk exposure data';
COMMENT ON COLUMN riski.exposure_data.area IS 'asset area';
COMMENT ON COLUMN riski.exposure_data.asset_ref IS 'A unique identifier (within the exposure model) for the asset at hand';
COMMENT ON COLUMN riski.exposure_data.exposure_model_id IS 'Foreign key to the exposure model';
COMMENT ON COLUMN riski.exposure_data.number_of_units IS 'number of assets, people etc.';
COMMENT ON COLUMN riski.exposure_data.taxonomy IS 'A reference to the taxonomy that should be used for the asset at hand';


CREATE TABLE riski.cost (
    id SERIAL PRIMARY KEY,
    exposure_data_id INTEGER NOT NULL,
    cost_type_id INTEGER NOT NULL,
    converted_cost float NOT NULL CONSTRAINT converted_cost_value
         CHECK(converted_cost >= 0.0),
    converted_retrofitted_cost float CONSTRAINT converted_retrofitted_cost_value
         CHECK(converted_retrofitted_cost >= 0.0),
    deductible_absolute float CONSTRAINT deductible_value
         CHECK(deductible_absolute >= 0.0),
    insurance_limit_absolute float CONSTRAINT insurance_limit_value
         CHECK(insurance_limit_absolute >= 0.0),
    UNIQUE (exposure_data_id, cost_type_id)
) TABLESPACE riski_ts;


CREATE TABLE riski.occupancy (
    id SERIAL PRIMARY KEY,
    exposure_data_id INTEGER NOT NULL,
    period VARCHAR NOT NULL,
    occupants float NOT NULL
) TABLESPACE riski_ts;

COMMENT ON TABLE riski.occupancy IS 'Occupancy for a given exposure data set';
COMMENT ON COLUMN riski.occupancy.exposure_data_id IS 'Foreign key to the exposure data set to which the occupancy data applies.';
COMMENT ON COLUMN riski.occupancy.period IS 'describes the occupancy data e.g. day, night etc.';
COMMENT ON COLUMN riski.occupancy.occupants IS 'number of occupants';


-- calculation points of interest with parameters extracted from site_model or hc
CREATE TABLE hzrdi.hazard_site (
    id SERIAL PRIMARY KEY,
    hazard_calculation_id INTEGER NOT NULL,
    location GEOGRAPHY(point) NOT NULL
) TABLESPACE hzrdi_ts;

------------------------------------------------------------------------
-- Constraints (foreign keys etc.) go here
------------------------------------------------------------------------
ALTER TABLE uiapi.oq_job ADD CONSTRAINT uiapi_oq_job_hazard_calculation
FOREIGN KEY (hazard_calculation_id) REFERENCES uiapi.hazard_calculation(id)
ON DELETE CASCADE;

ALTER TABLE uiapi.oq_job ADD CONSTRAINT uiapi_oq_job_risk_calculation
FOREIGN KEY (risk_calculation_id) REFERENCES uiapi.risk_calculation(id)
ON DELETE CASCADE;

ALTER TABLE uiapi.risk_calculation ADD CONSTRAINT uiapi_risk_calculation_hazard_output_fk
FOREIGN KEY (hazard_output_id) REFERENCES uiapi.output(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.risk_calculation ADD CONSTRAINT uiapi_risk_calculation_preloaded_exposure_model_fk
FOREIGN KEY (preloaded_exposure_model_id) REFERENCES riski.exposure_model(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.performance ADD CONSTRAINT uiapi_performance_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

ALTER TABLE uiapi.job_stats ADD CONSTRAINT uiapi_job_stats_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

ALTER TABLE uiapi.output ADD CONSTRAINT uiapi_output_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

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

-- gmf -> output FK
ALTER TABLE hzrdr.gmf
ADD CONSTRAINT hzrdr_gmf_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

-- gmf -> lt_realization FK
ALTER TABLE hzrdr.gmf
ADD CONSTRAINT hzrdr_gmf_lt_realization_fk
FOREIGN KEY (lt_realization_id) REFERENCES hzrdr.lt_realization(id)
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

-- hzrdr.lt_source_model -> uiapi.hazard_calculation FK
ALTER TABLE hzrdr.lt_source_model
ADD CONSTRAINT hzrdr_lt_model_hazard_calculation_fk
FOREIGN KEY (hazard_calculation_id)
REFERENCES uiapi.hazard_calculation(id)
ON DELETE CASCADE;

-- hzrdr.trt_model -> hzrdr.lt_source_model FK
ALTER TABLE hzrdr.trt_model
ADD CONSTRAINT hzrdr_trt_model_lt_source_model_fk
FOREIGN KEY (lt_model_id)
REFERENCES hzrdr.lt_source_model(id)
ON DELETE CASCADE;

-- hzrdr.source_info -> hzrdr.trt_model FK
ALTER TABLE hzrdr.source_info ADD CONSTRAINT hzrdr_source_info_trt_model_fk
FOREIGN KEY (trt_model_id) REFERENCES hzrdr.trt_model(id)
ON DELETE CASCADE;


-- hzrdr.assoc_lt_rlz_trt_model -> hzrdr.lt_realization FK
ALTER TABLE hzrdr.assoc_lt_rlz_trt_model
ADD CONSTRAINT hzrdr_assoc_lt_rlz_trt_model_fk1
FOREIGN KEY (rlz_id)
REFERENCES hzrdr.lt_realization(id)
ON DELETE CASCADE;

-- hzrdr.assoc_lt_rlz_trt_model -> hzrdr.trt_model FK
ALTER TABLE hzrdr.assoc_lt_rlz_trt_model
ADD CONSTRAINT hzrdr_trt_model_lt_source_model_fk2
FOREIGN KEY (trt_model_id)
REFERENCES hzrdr.trt_model(id)
ON DELETE CASCADE;

-- hzrdr.lt_realization -> hzrdr.lt_source_model FK
ALTER TABLE hzrdr.lt_realization
ADD CONSTRAINT hzrdr_lt_realization_lt_model_fk
FOREIGN KEY (lt_model_id) REFERENCES hzrdr.lt_source_model(id)
ON DELETE CASCADE;

-- hzrdr.ses_collection to uiapi.output FK
ALTER TABLE hzrdr.ses_collection
ADD CONSTRAINT hzrdr_ses_collection_output_fk
FOREIGN KEY (output_id)
REFERENCES uiapi.output(id)
ON DELETE CASCADE;

-- hzrdr.probabilistic_rupture to hzrdr.ses_collection FK
ALTER TABLE hzrdr.probabilistic_rupture
ADD CONSTRAINT hzrdr_probabilistic_rupture_ses_collection_fk
FOREIGN KEY (ses_collection_id) REFERENCES hzrdr.ses_collection(id)
ON DELETE CASCADE;

-- hzrdr.ses_rupture to hzrdr.probabilistic_rupture FK
ALTER TABLE hzrdr.ses_rupture
ADD CONSTRAINT hzrdr_ses_rupture_probabilistic_rupture_fk
FOREIGN KEY (rupture_id) REFERENCES hzrdr.probabilistic_rupture(id)
ON DELETE CASCADE;

-- hzrdr.ses_rupture to hzrdr.trt_model FK
ALTER TABLE hzrdr.probabilistic_rupture
ADD CONSTRAINT hzrdr_probabilistic_rupture_trt_model_fk
FOREIGN KEY (trt_model_id) REFERENCES hzrdr.trt_model(id)
ON DELETE CASCADE;

-- hzrdr.gmf_rupture -> hzrdi.imt FK
ALTER TABLE hzrdr.gmf_rupture
ADD CONSTRAINT hzrdr_gmf_rupture_imt_fk
FOREIGN KEY (imt)
REFERENCES hzrdi.imt(imt_str)
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
ADD CONSTRAINT riskr_event_loss_hazard_output_fk
FOREIGN KEY (hazard_output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.event_loss_data
ADD CONSTRAINT riskr_event_loss_data_sesrupture_fk
FOREIGN KEY (rupture_id) REFERENCES hzrdr.ses_rupture(id) ON DELETE CASCADE;

ALTER TABLE riskr.event_loss_data
ADD CONSTRAINT riskr_event_loss_data_event_loss_fk
FOREIGN KEY (event_loss_id) REFERENCES riskr.event_loss(id) ON DELETE CASCADE;

ALTER TABLE riskr.bcr_distribution_data
ADD CONSTRAINT riskr_bcr_distribution_data_bcr_distribution_fk
FOREIGN KEY (bcr_distribution_id) REFERENCES riskr.bcr_distribution(id) ON DELETE CASCADE;


-- Damage Distribution, Per Asset

ALTER TABLE riskr.dmg_dist_per_asset
ADD CONSTRAINT riskr_dmg_dist_per_asset_exposure_data_fk
FOREIGN KEY (exposure_data_id) REFERENCES riski.exposure_data(id) ON DELETE RESTRICT;


ALTER TABLE riski.exposure_data ADD CONSTRAINT
riski_exposure_data_exposure_model_fk FOREIGN KEY (exposure_model_id)
REFERENCES riski.exposure_model(id) ON DELETE CASCADE;

ALTER TABLE riski.occupancy ADD CONSTRAINT
riski_occupancy_exposure_data_fk FOREIGN KEY (exposure_data_id)
REFERENCES riski.exposure_data(id) ON DELETE CASCADE;

ALTER TABLE riski.cost_type ADD CONSTRAINT
riski_cost_type_exposure_model_fk FOREIGN KEY (exposure_model_id)
REFERENCES riski.exposure_model(id) ON DELETE CASCADE;

ALTER TABLE riski.cost ADD CONSTRAINT
riski_cost_exposure_data_fk FOREIGN KEY (exposure_data_id)
REFERENCES riski.exposure_data(id) ON DELETE CASCADE;

ALTER TABLE riski.cost ADD CONSTRAINT
riski_cost_cost_type_fk FOREIGN KEY (cost_type_id)
REFERENCES riski.cost_type(id) ON DELETE CASCADE;

-- hzrdi.hazard_site to uiapi.hazard_calculation FK
ALTER TABLE hzrdi.hazard_site
ADD CONSTRAINT hzrdi_hazard_site_hazard_calculation_fk
FOREIGN KEY (hazard_calculation_id)
REFERENCES uiapi.hazard_calculation(id)
ON DELETE CASCADE;

-- hzrdr.gmf_data to hzrdi.hazard_site FK
ALTER TABLE hzrdr.gmf_data
ADD CONSTRAINT hzrdr_gmf_data_hazard_site_fk
FOREIGN KEY (site_id)
REFERENCES hzrdi.hazard_site(id)
ON DELETE CASCADE;

ALTER TABLE hzrdr.gmf_data
ADD CONSTRAINT hzrdr_gmf_data_gmf_fk
FOREIGN KEY (gmf_id)
REFERENCES hzrdr.gmf(id)
ON DELETE CASCADE;


-- this function is used in the performance_view, cannot go in functions.sql
CREATE FUNCTION maxint(a INTEGER, b INTEGER) RETURNS INTEGER AS $$
SELECT CASE WHEN $1 > $2 THEN $1 ELSE $2 END;
$$ LANGUAGE SQL IMMUTABLE;

---------------------- views ----------------------------
-- convenience view to analyze the performance of the jobs;
-- for instance the slowest operations can be extracted with
-- SELECT DISTINCT ON (oq_job_id) * FROM uiapi.performance_view;
CREATE VIEW uiapi.performance_view AS
SELECT h.id AS calculation_id, description, 'hazard' AS job_type, p.* FROM (
     SELECT oq_job_id, operation,
     sum(duration) AS tot_duration,
     sum(duration)/maxint(count(distinct task_id)::int, 1) AS duration,
     max(pymemory)/1048576. AS pymemory, max(pgmemory)/1048576. AS pgmemory,
     count(*) AS counts
     FROM uiapi.performance
     GROUP BY oq_job_id, operation) AS p
INNER JOIN uiapi.oq_job AS o
ON p.oq_job_id=o.id
INNER JOIN uiapi.hazard_calculation AS h
ON h.id=o.hazard_calculation_id
UNION ALL
SELECT r.id AS calculation_id, description, 'risk' AS job_type, p.* FROM (
     SELECT oq_job_id, operation,
     sum(duration) AS tot_duration,
     sum(duration)/maxint(count(distinct task_id)::int, 1) AS duration,
     max(pymemory)/1048576. AS pymemory, max(pgmemory)/1048576. AS pgmemory,
     count(*) AS counts
     FROM uiapi.performance
     GROUP BY oq_job_id, operation) AS p
INNER JOIN uiapi.oq_job AS o
ON p.oq_job_id=o.id
INNER JOIN uiapi.risk_calculation AS r
ON r.id=o.risk_calculation_id;

-- gmf_data per job
CREATE VIEW hzrdr.gmf_data_job AS
   SELECT c.oq_job_id, a.*
   FROM hzrdr.gmf_data AS a
   INNER JOIN hzrdr.gmf AS b
   ON a.gmf_id=b.id
   INNER JOIN uiapi.output AS c
   ON b.output_id=c.id
   WHERE output_type='gmf';

------------------------------ INDEXES -----------------------------------------

-- hzrdi.hazard_site
CREATE UNIQUE INDEX hzrdi_hazard_site_location_hazard_calculation_uniq_idx
ON hzrdi.hazard_site(location, hazard_calculation_id);

CREATE INDEX hzrdi_hazard_site_hazard_calculation_idx
ON hzrdi.hazard_site(hazard_calculation_id);

-- hzrdi.site_model
CREATE INDEX hzrdi_site_model_job_id_idx ON hzrdi.site_model(job_id);

-- indexes for the uiapi.performance table
CREATE INDEX uiapi_performance_oq_job_id_idx ON uiapi.performance(oq_job_id);
CREATE INDEX uiapi_oq_job_user_name_idx ON uiapi.oq_job(user_name);
CREATE INDEX uiapi_performance_operation_idx ON uiapi.performance(operation);

CREATE INDEX uiapi_oq_job_status_running on uiapi.oq_job(status) WHERE status = 'running';

-- hzrdr indices on foreign keys
-- hazard map
CREATE INDEX hzrdr_hazard_map_output_id_idx on hzrdr.hazard_map(output_id);
-- hazard curve
CREATE INDEX hzrdr_hazard_curve_output_id_idx on hzrdr.hazard_curve(output_id);
CREATE INDEX hzrdr_hazard_curve_data_hazard_curve_id_idx on hzrdr.hazard_curve_data(hazard_curve_id);

-- hzrdr.assoc_lt_rlz_trt_model
CREATE UNIQUE INDEX hzrdr_assoc_lt_rlz_trt_model_uniq_idx ON 
hzrdr.assoc_lt_rlz_trt_model(rlz_id, trt_model_id);
 
-- gmf
CREATE INDEX hzrdr_gmf_output_id_idx on hzrdr.gmf(output_id);
CREATE INDEX hzrdr_gmf_lt_realization_idx on hzrdr.gmf(lt_realization_id);

-- uhs
CREATE INDEX hzrdr_uhs_output_id_idx on hzrdr.uhs(output_id);
CREATE INDEX hzrdr_uhs_data_uhs_id_idx on hzrdr.uhs_data(uhs_id);

-- ses
CREATE INDEX hzrdr_ses_collection_ouput_id_idx on hzrdr.ses_collection(output_id);

-- ses_rupture
CREATE UNIQUE INDEX hzrdr_ses_rupture_tag_uniq_idx ON hzrdr.ses_rupture(rupture_id, tag);
CREATE INDEX hzrdr_ses_rupture_ses_id_idx on hzrdr.ses_rupture(ses_id);
CREATE INDEX hzrdr_ses_rupture_tag_idx ON hzrdr.ses_rupture (tag);

-- disagg_result
CREATE INDEX hzrdr_disagg_result_location_idx on hzrdr.disagg_result using gist(location);
-- lt_realization
CREATE INDEX hzrdr_lt_model_hazard_calculation_id_idx on hzrdr.lt_source_model(hazard_calculation_id);

-- gmf_data
CREATE INDEX hzrdr_gmf_data_idx on hzrdr.gmf_data(site_id);
CREATE INDEX hzrdr_gmf_imt_idx on hzrdr.gmf_data(imt);
CREATE INDEX hzrdr_gmf_sa_period_idx on hzrdr.gmf_data(sa_period);
CREATE INDEX hzrdr_gmf_sa_damping_idx on hzrdr.gmf_data(sa_damping);
CREATE INDEX hzrdr_gmf_task_no_idx on hzrdr.gmf_data(task_no);

-- riskr indexes
CREATE INDEX riskr_loss_map_output_id_idx on riskr.loss_map(output_id);
CREATE INDEX riskr_loss_map_data_loss_map_id_idx on riskr.loss_map_data(loss_map_id);
CREATE INDEX riskr_loss_map_data_loss_map_data_idx on riskr.loss_map_data(asset_ref);
CREATE INDEX riskr_loss_curve_output_id_idx on riskr.loss_curve(output_id);
CREATE INDEX riskr_loss_curve_data_loss_curve_id_idx on riskr.loss_curve_data(loss_curve_id);
CREATE INDEX riskr_loss_curve_data_loss_curve_asset_ref_idx on riskr.loss_curve_data(asset_ref);
CREATE INDEX riskr_aggregate_loss_curve_data_loss_curve_id_idx on riskr.aggregate_loss_curve_data(loss_curve_id);

CREATE INDEX riskr_bcr_distribution_output_id_idx on riskr.bcr_distribution(output_id);
CREATE INDEX riskr_bcr_distribution_data_bcr_distribution_id_idx on riskr.bcr_distribution_data(bcr_distribution_id);

CREATE INDEX riskr_dmg_state_rc_id_idx on riskr.dmg_state(risk_calculation_id);
CREATE INDEX riskr_dmg_state_lsi_idx on riskr.dmg_state(lsi);

-- riski indexes
CREATE INDEX riski_exposure_data_site_idx ON riski.exposure_data USING gist(site);
CREATE INDEX riski_exposure_model_job_id_idx ON riski.exposure_model(job_id);
CREATE INDEX riski_exposure_data_taxonomy_idx ON riski.exposure_data(taxonomy);
CREATE INDEX riski_exposure_data_exposure_model_id_idx on riski.exposure_data(exposure_model_id);
CREATE INDEX riski_exposure_data_site_stx_idx ON riski.exposure_data(ST_X(geometry(site)));
CREATE INDEX riski_exposure_data_site_sty_idx ON riski.exposure_data(ST_Y(geometry(site)));
CREATE INDEX riski_cost_type_name_idx ON riski.cost_type(name);

--------------------------------- FUNCTIONS -------------------------------------

CREATE OR REPLACE FUNCTION format_exc(operation TEXT, error TEXT, tab_name TEXT) RETURNS TEXT AS $$
BEGIN
    RETURN operation || ': error: ' || error || ' (' || tab_name || ')';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION refresh_last_update() RETURNS TRIGGER
LANGUAGE plpgsql AS
$$
DECLARE
BEGIN
    NEW.last_update := timezone('UTC'::text, now());
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION refresh_last_update() IS
'Refresh the ''last_update'' time stamp whenever a row is updated.';


CREATE AGGREGATE array_concat(anyarray)(sfunc=array_cat, stype=anyarray, initcond='{}');


----- statistical helpers

CREATE TYPE moment AS (
  n bigint,
  sum double precision,
  sum2 double precision);

CREATE FUNCTION moment_from_array(double precision[])
RETURNS moment AS $$
SELECT sum(1), sum(v), sum(v * v) FROM unnest($1) AS v
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION stats_from_moment(moment)
RETURNS TABLE(n BIGINT, avg DOUBLE PRECISION, std DOUBLE PRECISION) AS $$
SELECT $1.n, $1.sum / $1.n,
       sqrt(($1.sum2 - $1.sum ^ 2 / $1.n) / ($1.n - 1))
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION moment_add(moment, moment)
RETURNS moment AS $$
SELECT $1.n + $2.n, $1.sum + $2.sum, $1.sum2 + $2.sum2
$$ LANGUAGE sql;

CREATE AGGREGATE moment_sum(moment)(
   sfunc=moment_add, stype=moment, initcond='(0,0,0)');

-- typical usage is a SELECT * FROM hzrdr.gmf_stats WHERE output_id=2;
CREATE VIEW hzrdr.gmf_stats AS
SELECT output_id, gmf_id, imt, sa_period, sa_damping,
      (stats).n, (stats).avg, (stats).std FROM (
  SELECT output_id, b.id as gmf_id, imt, sa_period, sa_damping,
  stats_from_moment(moment_sum(moment_from_array(gmvs))) AS stats
  FROM hzrdr.gmf_data as a
  INNER JOIN hzrdr.gmf AS b
  ON a.gmf_id=b.id
  GROUP BY output_id, b.id, imt, sa_period, sa_damping) AS x;

-- how many sources where done with respect to the total for each haz_calc
CREATE VIEW hzrdr.source_progress AS
SELECT a.hazard_calculation_id, sources_done, sources_todo FROM
   (SELECT y.hazard_calculation_id, count(x.id) AS sources_done
   FROM hzrdr.source_info AS x, hzrdr.lt_source_model AS y, hzrdr.trt_model AS z
   WHERE x.trt_model_id = z.id AND z.lt_model_id=y.id
   GROUP BY y.hazard_calculation_id) AS a,
   (SELECT y.hazard_calculation_id, sum(num_sources) AS sources_todo
   FROM hzrdr.lt_source_model AS y, hzrdr.trt_model AS z
   WHERE z.lt_model_id=y.id
   GROUP by y.hazard_calculation_id) AS b
WHERE a.hazard_calculation_id=b.hazard_calculation_id;


CREATE VIEW riskr.event_loss_view AS
SELECT b.tag as rupture_tag, c.id AS rupture_id,
   aggregate_loss, output_id, loss_type FROM
   riskr.event_loss_data AS a, hzrdr.ses_rupture AS b,
   hzrdr.probabilistic_rupture AS c, riskr.event_loss as d
WHERE a.rupture_id=b.id AND b.rupture_id=c.id AND a.event_loss_id=d.id;

/*
Security
*/

-- Please note that all OpenQuake database roles are a member of the
-- 'openquake' database group.
-- Granting certain privileges to the 'openquake' group hence applies to all
-- of our database users/roles.

GRANT USAGE ON SCHEMA hzrdi TO GROUP openquake;
GRANT USAGE ON SCHEMA hzrdr TO GROUP openquake;
GRANT USAGE ON SCHEMA riski TO GROUP openquake;
GRANT USAGE ON SCHEMA riskr TO GROUP openquake;
GRANT USAGE ON SCHEMA uiapi TO GROUP openquake;

GRANT ALL ON ALL SEQUENCES IN SCHEMA hzrdi TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA hzrdr TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA riski TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA riskr TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA uiapi TO GROUP openquake;

-- Users in the `openquake` group have read access to everything
GRANT SELECT ON ALL TABLES IN SCHEMA hzrdi TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA hzrdr TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA riski TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA riskr TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA uiapi TO GROUP openquake;
GRANT SELECT ON geography_columns          TO GROUP openquake;
GRANT SELECT ON geometry_columns           TO GROUP openquake;
GRANT SELECT ON spatial_ref_sys            TO GROUP openquake;

-- `oq_admin` has full SELECT/INSERT/UPDATE/DELETE access to all tables.
-- In fact, `oq_admin` is the only user that can delete records
-- with the exception the uiapi.performance table.
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA hzrdi TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA hzrdr TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA riski TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA riskr TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA uiapi TO oq_admin;

GRANT ALL ON SCHEMA hzrdi TO oq_admin;
GRANT ALL ON SCHEMA hzrdr TO oq_admin;
GRANT ALL ON SCHEMA riski TO oq_admin;
GRANT ALL ON SCHEMA riskr TO oq_admin;
GRANT ALL ON SCHEMA uiapi TO oq_admin;

----------------------------------------------
-- Specific permissions for individual tables:
----------------------------------------------

-- hzrdi schema
GRANT SELECT,INSERT ON hzrdi.hazard_site            TO oq_job_init;
GRANT SELECT,INSERT ON hzrdi.site_model             TO oq_job_init;

-- hzrdr schema
GRANT SELECT,INSERT        ON hzrdr.hazard_curve      TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON hzrdr.hazard_curve_data TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.gmf               TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.gmf_data          TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.disagg_result     TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON hzrdr.hazard_map        TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.uhs               TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.uhs_data          TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON hzrdr.lt_realization    TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.lt_source_model   TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON hzrdr.trt_model         TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.source_info       TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.assoc_lt_rlz_trt_model TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.ses_collection    TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.ses_rupture       TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.probabilistic_rupture TO oq_job_init;

-- riski schema
GRANT SELECT,INSERT ON ALL TABLES IN SCHEMA riski   TO oq_job_init;
GRANT UPDATE        ON riski.occupancy              TO oq_job_init;

-- riskr schema
GRANT SELECT,INSERT,UPDATE ON riskr.loss_curve                TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_curve_data           TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.aggregate_loss_curve_data TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_map                  TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_map_data             TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_fraction             TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_fraction_data        TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.aggregate_loss            TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.bcr_distribution          TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.bcr_distribution_data     TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.dmg_state                 TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.dmg_dist_per_asset        TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.dmg_dist_per_taxonomy     TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.dmg_dist_total            TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.event_loss                TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.event_loss_data           TO oq_job_init;

-- uiapi schema
GRANT SELECT,INSERT,UPDATE ON uiapi.oq_job             TO oq_job_init;
-- oq_job_init is granted write access to record job start time and other job stats at job init time
GRANT SELECT,INSERT,UPDATE ON uiapi.job_stats          TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON uiapi.job_stats          TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON uiapi.hazard_calculation TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON uiapi.risk_calculation   TO oq_job_init;

GRANT SELECT,INSERT,UPDATE ON uiapi.output             TO oq_job_init;
GRANT SELECT,INSERT,DELETE ON uiapi.performance        TO oq_job_init;
