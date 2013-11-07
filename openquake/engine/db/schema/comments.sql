/*
  Copyright (c) 2010-2013, GEM Foundation.

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


-- schemas ------------------------------------------------------
COMMENT ON SCHEMA admin IS 'Administrative data';
COMMENT ON SCHEMA hzrdi IS 'Hazard input model';
COMMENT ON SCHEMA hzrdr IS 'Hazard result data';
COMMENT ON SCHEMA riski IS 'Risk input model';
COMMENT ON SCHEMA riskr IS 'Risk result data';
COMMENT ON SCHEMA uiapi IS 'Data required by the API presented to the various OpenQuake UIs';



-- admin schema tables ------------------------------------------
COMMENT ON TABLE admin.revision_info IS 'Facilitates the keeping of revision information for the OpenQuake database and/or its artefacts (schemas, tables etc.)';
COMMENT ON COLUMN admin.revision_info.artefact IS 'The name of the database artefact for which we wish to store revision information.';
COMMENT ON COLUMN admin.revision_info.revision IS 'The revision information for the associated database artefact.';
COMMENT ON COLUMN admin.revision_info.step IS 'A simple counter that will be used to facilitate schema upgrades and/or data migration.';
COMMENT ON COLUMN admin.revision_info.last_update IS 'The date/time when the revision information was last updated. Please note: this time stamp is not refreshed automatically. It is expected that schema/data migration scripts will modify this as appropriate.';


-- hzrdi schema tables ------------------------------------------

COMMENT ON TABLE hzrdi.parsed_source IS 'Stores parsed hazard input model sources in serialized python object tree format';
COMMENT ON COLUMN hzrdi.parsed_source.nrml IS 'NRML object representing the source';
COMMENT ON COLUMN hzrdi.parsed_source.source_type IS 'The source''s seismic input type: can be one of: area, point, complex or simple.';


COMMENT ON TABLE hzrdi.parsed_rupture_model IS 'Stores parsed hazard rupture model in serialized python object tree format';
COMMENT ON COLUMN hzrdi.parsed_rupture_model.nrml IS 'NRML object representing the rupture';
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

COMMENT ON TABLE hzrdr.hazard_map IS 'A complete hazard map, for a given IMT and PoE';
COMMENT ON COLUMN hzrdr.hazard_map.poe IS 'Probability of exceedence';
COMMENT ON COLUMN hzrdr.hazard_map.statistics IS 'Statistic type, one of:
    - Median   (median)
    - Quantile (quantile)';
COMMENT ON COLUMN hzrdr.hazard_map.quantile IS 'The quantile level for quantile statistical data.';


-- riski schema tables ------------------------------------------
COMMENT ON TABLE riski.exposure_data IS 'Per-asset risk exposure data';
COMMENT ON COLUMN riski.exposure_data.area IS 'asset area';
COMMENT ON COLUMN riski.exposure_data.asset_ref IS 'A unique identifier (within the exposure model) for the asset at hand';
COMMENT ON COLUMN riski.exposure_data.exposure_model_id IS 'Foreign key to the exposure model';
COMMENT ON COLUMN riski.exposure_data.number_of_units IS 'number of assets, people etc.';
COMMENT ON COLUMN riski.exposure_data.taxonomy IS 'A reference to the taxonomy that should be used for the asset at hand';


COMMENT ON TABLE riski.exposure_model IS 'A risk exposure model';
COMMENT ON COLUMN riski.exposure_model.area_type IS 'area type. one of: aggregated or per_asset';
COMMENT ON COLUMN riski.exposure_model.area_unit IS 'area unit of measure e.g. sqm';
COMMENT ON COLUMN riski.exposure_model.category IS 'The risk category modelled';
COMMENT ON COLUMN riski.exposure_model.description IS 'An optional description of the risk exposure model at hand';

COMMENT ON COLUMN riski.exposure_model.name IS 'The exposure model name';

COMMENT ON COLUMN riski.exposure_model.taxonomy_source IS 'the taxonomy system used to classify the assets';


COMMENT ON TABLE riski.occupancy IS 'Occupancy for a given exposure data set';
COMMENT ON COLUMN riski.occupancy.exposure_data_id IS 'Foreign key to the exposure data set to which the occupancy data applies.';
COMMENT ON COLUMN riski.occupancy.period IS 'describes the occupancy data e.g. day, night etc.';
COMMENT ON COLUMN riski.occupancy.occupants IS 'number of occupants';

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
COMMENT ON COLUMN riskr.loss_curve_data.asset_value IS 'The value of the asset';
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

COMMENT ON TABLE uiapi.oq_job IS 'Date related to an OpenQuake job that was created in the UI.';
COMMENT ON COLUMN uiapi.oq_job.job_pid IS 'The process id (PID) of the OpenQuake engine runner process';
COMMENT ON COLUMN uiapi.oq_job.supervisor_pid IS 'The process id (PID) of the supervisor for this OpenQuake job';
COMMENT ON COLUMN uiapi.oq_job.status IS 'One of: pending, running, failed or succeeded.';
COMMENT ON COLUMN uiapi.oq_job.duration IS 'The job''s duration in seconds (only available once the jobs terminates).';

COMMENT ON TABLE uiapi.performance IS 'Tracks task performance';
COMMENT ON COLUMN uiapi.performance.duration IS 'Duration of the operation in seconds';
COMMENT ON COLUMN uiapi.performance.pymemory IS 'Memory occupation in Python (Mbytes)';
COMMENT ON COLUMN uiapi.performance.pgmemory IS 'Memory occupation in Postgres (Mbytes)';


COMMENT ON TABLE uiapi.job_stats IS 'Tracks various job statistics';
COMMENT ON COLUMN uiapi.job_stats.num_sites IS 'The number of total sites in the calculation';
COMMENT ON COLUMN uiapi.job_stats.disk_space IS 'How much the disk space occupation increased during the computation (in bytes)';


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
