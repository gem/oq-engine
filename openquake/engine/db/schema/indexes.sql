/*
  Indexes for the OpenQuake database.

    Copyright (c) 2010-2012, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- admin.oq_user
CREATE UNIQUE INDEX admin_oq_user_user_name_uniq_idx ON admin.oq_user(user_name);

-- admin.revision_info
CREATE UNIQUE INDEX admin_revision_info_artefact_uniq_idx ON admin.revision_info(artefact);

-- eqcat.catalog
CREATE INDEX eqcat_catalog_agency_idx on eqcat.catalog(agency);
CREATE INDEX eqcat_catalog_time_idx on eqcat.catalog(time);
CREATE INDEX eqcat_catalog_depth_idx on eqcat.catalog(depth);
CREATE INDEX eqcat_catalog_point_idx ON eqcat.catalog USING gist(point);

-- hzrdi.site_model
CREATE INDEX hzrdi_site_model_input_id_idx ON hzrdi.site_model(input_id);

-- index for the 'owner_id' foreign key
CREATE INDEX eqcat_catalog_owner_id_idx on eqcat.catalog(owner_id);
CREATE INDEX uiapi_input_owner_id_idx on uiapi.input(owner_id);

CREATE INDEX uiapi_oq_job_owner_id_idx on uiapi.oq_job(owner_id);
CREATE INDEX uiapi_oq_job_profile_owner_id_idx on uiapi.oq_job_profile(owner_id);
CREATE INDEX uiapi_oq_job_status_running on uiapi.oq_job(status) WHERE status = 'running';
CREATE INDEX uiapi_output_owner_id_idx on uiapi.output(owner_id);

-- hzrdr indices on foreign keys
-- hazard map
CREATE INDEX hzrdr_hazard_map_output_id_idx on hzrdr.hazard_map(output_id);
-- hazard curve
CREATE INDEX hzrdr_hazard_curve_output_id_idx on hzrdr.hazard_curve(output_id);
CREATE INDEX hzrdr_hazard_curve_data_hazard_curve_id_idx on hzrdr.hazard_curve_data(hazard_curve_id);
-- gmf
CREATE INDEX hzrdr_gmf_data_output_id_idx on hzrdr.gmf_data(output_id);

CREATE INDEX hzrdr_gmf_collection_output_id_idx on hzrdr.gmf_collection(output_id);
CREATE INDEX hzrdr_gmf_collection_lt_realization_idx on hzrdr.gmf_collection(lt_realization_id);
CREATE INDEX hzrdr_gmf_set_gmf_collection_idx on hzrdr.gmf_set(gmf_collection_id);
CREATE INDEX hzrdr_gmf_gmf_set_idx on hzrdr.gmf(gmf_set_id);
CREATE INDEX hzrdr_gmf_location_idx on hzrdr.gmf using gist(location);
-- uhs
CREATE INDEX hzrdr_uh_spectra_output_id_idx on hzrdr.uh_spectra(output_id);
CREATE INDEX hzrdr_uh_spectrum_uh_spectra_id_idx on hzrdr.uh_spectrum(uh_spectra_id);
CREATE INDEX hzrdr_uh_spectrum_data_uh_spectrum_id_idx on hzrdr.uh_spectrum_data(uh_spectrum_id);
-- ses
CREATE INDEX hzrdr_ses_collection_ouput_id_idx on hzrdr.ses_collection(output_id);
CREATE INDEX hzrdr_ses_ses_collection_id_idx on hzrdr.ses(ses_collection_id);
CREATE INDEX hzrdr_ses_rupture_ses_id_idx on hzrdr.ses_rupture(ses_id);
-- disagg_result
CREATE INDEX hzrdr_disagg_result_location_idx on hzrdr.disagg_result using gist(location);
-- lt_realization
CREATE INDEX hzrdr_lt_realization_hazard_calculation_id_idx on hzrdr.lt_realization(hazard_calculation_id);

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

-- oqmif indexes
CREATE INDEX oqmif_exposure_data_site_idx ON oqmif.exposure_data USING gist(site);
CREATE INDEX oqmif_exposure_data_taxonomy_idx ON oqmif.exposure_data(taxonomy);
CREATE INDEX oqmif_exposure_data_exposure_model_id_idx on oqmif.exposure_data(exposure_model_id);

-- uiapi indexes
CREATE INDEX uiapi_job2profile_oq_job_profile_id_idx on uiapi.job2profile(oq_job_profile_id);
CREATE INDEX uiapi_job2profile_job_id_idx on uiapi.job2profile(oq_job_id);
CREATE INDEX uiapi_input_model_content_id_idx on uiapi.input(model_content_id);

-- htemp indexes
CREATE INDEX htemp_source_progress_lt_realization_id_idx on htemp.source_progress(lt_realization_id);
CREATE INDEX htemp_hazard_curve_progress_lt_realization_id_idx on htemp.hazard_curve_progress(lt_realization_id);
