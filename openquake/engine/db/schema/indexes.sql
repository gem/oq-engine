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


-- admin.revision_info
CREATE UNIQUE INDEX admin_revision_info_artefact_uniq_idx ON admin.revision_info(artefact);

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

-- gmf
CREATE INDEX hzrdr_gmf_output_id_idx on hzrdr.gmf(output_id);
CREATE INDEX hzrdr_gmf_lt_realization_idx on hzrdr.gmf(lt_realization_id);

-- uhs
CREATE INDEX hzrdr_uhs_output_id_idx on hzrdr.uhs(output_id);
CREATE INDEX hzrdr_uhs_data_uhs_id_idx on hzrdr.uhs_data(uhs_id);
-- ses
CREATE INDEX hzrdr_ses_collection_ouput_id_idx on hzrdr.ses_collection(output_id);
CREATE INDEX hzrdr_ses_ses_collection_id_idx on hzrdr.ses(ses_collection_id);
CREATE INDEX hzrdr_ses_rupture_ses_id_idx on hzrdr.ses_rupture(ses_id);
CREATE INDEX hzrdr_ses_rupture_tag_idx ON hzrdr.ses_rupture (tag);

-- disagg_result
CREATE INDEX hzrdr_disagg_result_location_idx on hzrdr.disagg_result using gist(location);
-- lt_realization
CREATE INDEX hzrdr_lt_realization_hazard_calculation_id_idx on hzrdr.lt_realization(hazard_calculation_id);

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
