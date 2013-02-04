/*
  Documentation for the OpenQuake database schema.
  Please keep these alphabetical by table.

    Copyright (c) 2010-2012, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/



-- schemas ------------------------------------------------------
COMMENT ON SCHEMA admin IS 'Administrative data';
COMMENT ON SCHEMA eqcat IS 'Earthquake catalog';
COMMENT ON SCHEMA hzrdi IS 'Hazard input model';
COMMENT ON SCHEMA hzrdr IS 'Hazard result data';
COMMENT ON SCHEMA oqmif IS 'OpenQuake tables for interfacing with external parties';
COMMENT ON SCHEMA riski IS 'Risk input model';
COMMENT ON SCHEMA riskr IS 'Risk result data';
COMMENT ON SCHEMA uiapi IS 'Data required by the API presented to the various OpenQuake UIs';



-- admin schema tables ------------------------------------------
COMMENT ON TABLE admin.organization IS 'An organization that is utilising the OpenQuake database';


COMMENT ON TABLE admin.oq_user IS 'An OpenQuake user that is utilising the OpenQuake database';
COMMENT ON COLUMN admin.oq_user.data_is_open IS 'Whether the data owned by the user is visible to the general public.';


COMMENT ON TABLE admin.revision_info IS 'Facilitates the keeping of revision information for the OpenQuake database and/or its artefacts (schemas, tables etc.)';
COMMENT ON COLUMN admin.revision_info.artefact IS 'The name of the database artefact for which we wish to store revision information.';
COMMENT ON COLUMN admin.revision_info.revision IS 'The revision information for the associated database artefact.';
COMMENT ON COLUMN admin.revision_info.step IS 'A simple counter that will be used to facilitate schema upgrades and/or data migration.';
COMMENT ON COLUMN admin.revision_info.last_update IS 'The date/time when the revision information was last updated. Please note: this time stamp is not refreshed automatically. It is expected that schema/data migration scripts will modify this as appropriate.';



-- eqcat schema tables ------------------------------------------
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

COMMENT ON VIEW eqcat.catalog_allfields IS 'A global catalog view, needed for geonode integration';



-- hzrdi schema tables ------------------------------------------

COMMENT ON TABLE hzrdi.parsed_source IS 'Stores parsed hazard input model sources in serialized python object tree format';
COMMENT ON COLUMN hzrdi.parsed_source.nrml IS 'NRML object representing the source';
COMMENT ON COLUMN hzrdi.parsed_source.input_id IS 'The foreign key to the associated input model file';
COMMENT ON COLUMN hzrdi.parsed_source.source_type IS 'The source''s seismic input type: can be one of: area, point, complex or simple.';
COMMENT ON COLUMN hzrdi.parsed_source.polygon IS 'The surface projection (2D)
of the "rupture enclosing" polygon for each source.
This is relevant to all source types, including point sources.
When considering a parsed_source record given a minimum integration distance,
use this polygon in distance calculations.';


COMMENT ON TABLE hzrdi.parsed_rupture_model IS 'Stores parsed hazard rupture model in serialized python object tree format';
COMMENT ON COLUMN hzrdi.parsed_rupture_model.nrml IS 'NRML object representing the rupture';
COMMENT ON COLUMN hzrdi.parsed_rupture_model.input_id IS 'The foreign key to the associated input rupture model file';
COMMENT ON COLUMN hzrdi.parsed_rupture_model.rupture_type IS 'The rupture''s seismic input type: can be one of: complex_fault or simple_fault.';



-- hzrdr schema tables ------------------------------------------
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


COMMENT ON TABLE hzrdr.hazard_curve_data IS 'Holds location/POE data for hazard curves';
COMMENT ON COLUMN hzrdr.hazard_curve_data.hazard_curve_id IS 'The foreign key to the hazard curve record for this node.';
COMMENT ON COLUMN hzrdr.hazard_curve_data.poes IS 'Probabilities of exceedence.';


COMMENT ON TABLE hzrdr.gmf_data IS 'Holds data for the ground motion field';
COMMENT ON COLUMN hzrdr.gmf_data.ground_motion IS 'Ground motion for a specific site';
COMMENT ON COLUMN hzrdr.gmf_data.location IS 'Site coordinates';


COMMENT ON TABLE hzrdr.hazard_map IS 'A complete hazard map, for a given IMT and PoE';
COMMENT ON COLUMN hzrdr.hazard_map.poe IS 'Probability of exceedence';
COMMENT ON COLUMN hzrdr.hazard_map.statistics IS 'Statistic type, one of:
    - Median   (median)
    - Quantile (quantile)';
COMMENT ON COLUMN hzrdr.hazard_map.quantile IS 'The quantile level for quantile statistical data.';


-- uhs
COMMENT ON TABLE hzrdr.uh_spectra IS 'Uniform Hazard Spectra

A collection of Uniform Hazard Spectrum which share a set of periods.
A UH Spectrum has a PoE (Probability of Exceedence) and is conceptually
composed of a set of 2D matrices, 1 matrix per site/point of interest.
Each 2D matrix has a number of rows equal to `realizations` and a number of
columns equal ot the number of `periods`.';
COMMENT ON COLUMN hzrdr.uh_spectra.periods IS 'There should be at least 1 period value defined.';
COMMENT ON TABLE hzrdr.uh_spectrum IS 'Uniform Hazard Spectrum

* "Uniform" meaning "the same PoE"
* "Spectrum" because it covers a range/band of periods/frequencies';
COMMENT ON TABLE hzrdr.uh_spectrum_data IS 'Uniform Hazard Spectrum Data

A single "row" of data in a UHS matrix for a specific site/point of interest.';
COMMENT ON COLUMN hzrdr.uh_spectrum_data.realization IS 'Logic tree sample number for this calculation result, from 0 to N.';



-- oqmif schema tables ------------------------------------------
COMMENT ON TABLE oqmif.exposure_data IS 'Per-asset risk exposure data';
COMMENT ON COLUMN oqmif.exposure_data.area IS 'asset area';
COMMENT ON COLUMN oqmif.exposure_data.asset_ref IS 'A unique identifier (within the exposure model) for the asset at hand';
COMMENT ON COLUMN oqmif.exposure_data.deductible IS 'insurance deductible';
COMMENT ON COLUMN oqmif.exposure_data.coco IS 'contents cost';
COMMENT ON COLUMN oqmif.exposure_data.ins_limit IS 'insurance coverage limit';
COMMENT ON COLUMN oqmif.exposure_data.exposure_model_id IS 'Foreign key to the exposure model';
COMMENT ON COLUMN oqmif.exposure_data.last_update IS 'Date/time of the last change of the exposure data for the asset at hand';
COMMENT ON COLUMN oqmif.exposure_data.number_of_units IS 'number of assets, people etc.';
COMMENT ON COLUMN oqmif.exposure_data.reco IS 'retrofitting cost';
COMMENT ON COLUMN oqmif.exposure_data.stco IS 'structural cost';
COMMENT ON COLUMN oqmif.exposure_data.taxonomy IS 'A reference to the taxonomy that should be used for the asset at hand';


COMMENT ON TABLE oqmif.exposure_model IS 'A risk exposure model';
COMMENT ON COLUMN oqmif.exposure_model.area_type IS 'area type. one of: aggregated or per_asset';
COMMENT ON COLUMN oqmif.exposure_model.area_unit IS 'area unit of measure e.g. sqm';
COMMENT ON COLUMN oqmif.exposure_model.category IS 'The risk category modelled';
COMMENT ON COLUMN oqmif.exposure_model.coco_type IS 'contents cost type, one of: aggregated, per_area or per_asset';
COMMENT ON COLUMN oqmif.exposure_model.coco_unit IS 'unit of measure for the contents type';
COMMENT ON COLUMN oqmif.exposure_model.description IS 'An optional description of the risk exposure model at hand';
COMMENT ON COLUMN oqmif.exposure_model.input_id IS 'The foreign key to the associated input model file';
COMMENT ON COLUMN oqmif.exposure_model.last_update IS 'Date/time of the last change of the model at hand';
COMMENT ON COLUMN oqmif.exposure_model.name IS 'The exposure model name';
COMMENT ON COLUMN oqmif.exposure_model.owner_id IS 'The foreign key to the user who owns the exposure model in question';
COMMENT ON COLUMN oqmif.exposure_model.reco_type IS 'retrofitting cost type, one of: aggregated, per_area or per_asset';
COMMENT ON COLUMN oqmif.exposure_model.reco_unit IS 'unit of measure for the retrofitting type';
COMMENT ON COLUMN oqmif.exposure_model.stco_type IS 'structural cost type, one of: aggregated, per_area or per_asset';
COMMENT ON COLUMN oqmif.exposure_model.stco_unit IS 'unit of measure for the structural type';
COMMENT ON COLUMN oqmif.exposure_model.taxonomy_source IS 'the taxonomy system used to classify the assets';


COMMENT ON TABLE oqmif.occupancy IS 'Occupancy for a given exposure data set';
COMMENT ON COLUMN oqmif.occupancy.exposure_data_id IS 'Foreign key to the exposure data set to which the occupancy data applies.';
COMMENT ON COLUMN oqmif.occupancy.description IS 'describes the occupancy data e.g. day, night etc.';
COMMENT ON COLUMN oqmif.occupancy.occupants IS 'number of occupants';

-- riskr schema tables ------------------------------------------
COMMENT ON TABLE riskr.loss_map IS 'Holds metadata for loss maps.';
COMMENT ON COLUMN riskr.loss_map.output_id IS 'The foreign key to the output record that represents the corresponding loss map.';
COMMENT ON COLUMN riskr.loss_map.poe IS 'Probability of exceedance (for probabilistic loss maps)';


COMMENT ON TABLE riskr.loss_map_data IS 'Holds an asset, its position and a value plus (for non-scenario maps) the standard deviation for its loss.';
COMMENT ON COLUMN riskr.loss_map_data.loss_map_id IS 'The foreign key to the loss map';
COMMENT ON COLUMN riskr.loss_map_data.asset_ref IS 'The asset reference';
COMMENT ON COLUMN riskr.loss_map_data.location IS 'The position of the asset';
COMMENT ON COLUMN riskr.loss_map_data.value IS 'The value of the loss';
COMMENT ON COLUMN riskr.loss_map_data.std_dev IS 'The standard deviation of the loss (for scenario maps, for non-scenario maps the standard deviation is NULL)';


COMMENT ON TABLE riskr.loss_curve IS 'Holds the parameters common to a set of loss curves.';
COMMENT ON COLUMN riskr.loss_curve.output_id IS 'The foreign key to the output record that represents the corresponding loss curve.';
COMMENT ON COLUMN riskr.loss_curve.aggregate IS 'Is the curve an aggregate curve?';


COMMENT ON TABLE riskr.loss_curve_data IS 'Holds the probabilities of exceedance for a given loss curve.';
COMMENT ON COLUMN riskr.loss_curve_data.loss_curve_id IS 'The foreign key to the curve record to which the loss curve data belongs';
COMMENT ON COLUMN riskr.loss_curve_data.asset_ref IS 'The asset id';
COMMENT ON COLUMN riskr.loss_curve_data.location IS 'The position of the asset';
COMMENT ON COLUMN riskr.loss_curve_data.losses IS 'Losses';
COMMENT ON COLUMN riskr.loss_curve_data.loss_ratios IS 'Loss ratios';
COMMENT ON COLUMN riskr.loss_curve_data.poes IS 'Probabilities of exceedence';


COMMENT ON TABLE riskr.aggregate_loss_curve_data IS 'Holds the probabilities of exceedance for the whole exposure model.';
COMMENT ON COLUMN riskr.aggregate_loss_curve_data.loss_curve_id IS 'The foreign key to the loss curve record to which the aggregate loss curve data belongs';
COMMENT ON COLUMN riskr.aggregate_loss_curve_data.losses IS 'Losses';
COMMENT ON COLUMN riskr.aggregate_loss_curve_data.poes IS 'Probabilities of exceedence';

COMMENT ON TABLE riskr.bcr_distribution IS 'Holds metadata for the benefit-cost ratio distribution';
COMMENT ON COLUMN riskr.bcr_distribution.output_id IS 'The foreign key to the output record that represents the corresponding BCR distribution.';

COMMENT ON TABLE riskr.bcr_distribution_data IS 'Holds the actual data for the BCR distribution';
COMMENT ON COLUMN riskr.bcr_distribution_data.bcr_distribution_id IS 'The foreign key to the record to which the BCR distribution data belongs';
COMMENT ON COLUMN riskr.bcr_distribution_data.asset_ref IS 'The asset id';
COMMENT ON COLUMN riskr.bcr_distribution_data.average_annual_loss_original IS 'The Expected annual loss computed by using the original model';
COMMENT ON COLUMN riskr.bcr_distribution_data.average_annual_loss_retrofitted IS 'The Expected annual loss computed by using the retrofitted model';
COMMENT ON COLUMN riskr.bcr_distribution_data.bcr IS 'The actual benefit-cost ratio';

COMMENT ON TABLE riskr.dmg_state IS 'Holds the damage_states associated to a given output';

-- uiapi schema tables ------------------------------------------
COMMENT ON TABLE uiapi.input IS 'A single OpenQuake input file imported by the user';
COMMENT ON COLUMN uiapi.input.digest IS '32 byte md5sum digest, used to detect identical input model files';
COMMENT ON COLUMN uiapi.input.input_type IS 'Input file type, one of:
    - source model file (source)
    - source logic tree (lt_source)
    - GSIM (Ground Shaking Intensity Model) logic tree (lt_gsim)
    - exposure file (exposure)
    - vulnerability file (vulnerability)
    - rupture file (rupture)';
COMMENT ON COLUMN uiapi.input.path IS 'The full path of the input file on the server';
COMMENT ON COLUMN uiapi.input.size IS 'Number of bytes in file';

COMMENT ON TABLE uiapi.input2job IS 'Associate inputs and jobs';

COMMENT ON TABLE uiapi.job2profile IS 'Associate jobs with their profiles';

COMMENT ON TABLE uiapi.oq_job IS 'Date related to an OpenQuake job that was created in the UI.';
COMMENT ON COLUMN uiapi.oq_job.job_pid IS 'The process id (PID) of the OpenQuake engine runner process';
COMMENT ON COLUMN uiapi.oq_job.supervisor_pid IS 'The process id (PID) of the supervisor for this OpenQuake job';
COMMENT ON COLUMN uiapi.oq_job.status IS 'One of: pending, running, failed or succeeded.';
COMMENT ON COLUMN uiapi.oq_job.duration IS 'The job''s duration in seconds (only available once the jobs terminates).';


COMMENT ON TABLE uiapi.job_stats IS 'Tracks various job statistics';
COMMENT ON COLUMN uiapi.job_stats.num_sites IS 'The number of total sites in the calculation';
COMMENT ON COLUMN uiapi.job_stats.num_realizations IS 'The number of logic tree samples in the calculation';


COMMENT ON TABLE uiapi.oq_job_profile IS 'Holds the parameters needed to invoke the OpenQuake engine.';
COMMENT ON COLUMN uiapi.oq_job_profile.calc_mode IS 'One of: classical, event_based, scenario, disaggregation, uhs, classical_bcr or event_based_bcr.';
COMMENT ON COLUMN uiapi.oq_job_profile.histories IS 'Number of seismicity histories';
COMMENT ON COLUMN uiapi.oq_job_profile.force_inputs IS 'If true: parse model inputs and write them to the database no matter what';
COMMENT ON COLUMN uiapi.oq_job_profile.imls IS 'Intensity measure levels';
COMMENT ON COLUMN uiapi.oq_job_profile.imt IS 'Intensity measure type, one of:
    - peak ground acceleration (pga)
    - spectral acceleration (sa)
    - peak ground velocity (pgv)
    - peak ground displacement (pgd)
    - Arias Intensity (ia)
    - relative significant duration (rsd)
    - Modified Mercalli Intensity';
COMMENT ON COLUMN uiapi.oq_job_profile.job_type IS '"hazard" and/or "risk"';
COMMENT ON COLUMN uiapi.oq_job_profile.lrem_steps_per_interval IS 'Loss Ration Exceedence Matrix steps per interval. Only used for Classical/Classical BCR Risk calculations.';
COMMENT ON COLUMN uiapi.oq_job_profile.poes IS 'Probabilities of exceedence';
COMMENT ON COLUMN uiapi.oq_job_profile.region_grid_spacing IS 'Desired cell size (in degrees), used when splitting up the region of interest. This effectively defines the resolution of the job. (Smaller grid spacing means more sites and thus more calculations.)';
COMMENT ON COLUMN uiapi.oq_job_profile.region IS 'Region of interest for the calculation (Polygon)';
COMMENT ON COLUMN uiapi.oq_job_profile.sites IS 'Sites of interest for the calculation (MultiPoint)';


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


COMMENT ON TABLE uiapi.src2ltsrc IS '
Associate an "lt_source" type input (a logic tree source) with "source"
type inputs (hazard sources referenced by the logic tree source).
This is needed for worker-side logic tree processing.';


-- uiapi.error_msg
COMMENT ON TABLE uiapi.error_msg IS 'A place to store error information in the case of a job failure.';
COMMENT ON COLUMN uiapi.error_msg.brief IS 'Summary of the error message.';
COMMENT ON COLUMN uiapi.error_msg.detailed IS 'The full error message.';
