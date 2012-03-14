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

-- hzrdi.fault_edge
CREATE INDEX hzrdi_fault_edge_bottom_idx ON hzrdi.fault_edge USING gist(bottom);
CREATE INDEX hzrdi_fault_edge_top_idx ON hzrdi.fault_edge USING gist(top);

-- hzrdi.rupture
CREATE INDEX hzrdi_rupture_point_idx ON hzrdi.rupture USING gist(point);

-- hzrdi.simple_fault
CREATE INDEX hzrdi_simple_fault_edge_idx ON hzrdi.simple_fault USING gist(edge);
CREATE INDEX hzrdi_simple_fault_outline_idx ON hzrdi.simple_fault USING gist(outline);

-- hzrdi.source
CREATE INDEX hzrdi_source_area_idx ON hzrdi.source USING gist(area);
CREATE INDEX hzrdi_source_point_idx ON hzrdi.source USING gist(point);

-- index for the 'owner_id' foreign key
CREATE INDEX eqcat_catalog_owner_id_idx on eqcat.catalog(owner_id);
CREATE INDEX hzrdi_complex_fault_owner_id_idx on hzrdi.complex_fault(owner_id);
CREATE INDEX hzrdi_fault_edge_owner_id_idx on hzrdi.fault_edge(owner_id);
CREATE INDEX hzrdi_focal_mechanism_owner_id_idx on hzrdi.focal_mechanism(owner_id);
CREATE INDEX hzrdi_mfd_evd_owner_id_idx on hzrdi.mfd_evd(owner_id);
CREATE INDEX hzrdi_mfd_tgr_owner_id_idx on hzrdi.mfd_tgr(owner_id);
CREATE INDEX hzrdi_r_depth_distr_owner_id_idx on hzrdi.r_depth_distr(owner_id);
CREATE INDEX hzrdi_r_rate_mdl_owner_id_idx on hzrdi.r_rate_mdl(owner_id);
CREATE INDEX hzrdi_rupture_owner_id_idx on hzrdi.rupture(owner_id);
CREATE INDEX hzrdi_simple_fault_owner_id_idx on hzrdi.simple_fault(owner_id);
CREATE INDEX hzrdi_source_owner_id_idx on hzrdi.source(owner_id);

CREATE INDEX uiapi_input_owner_id_idx on uiapi.input(owner_id);

CREATE INDEX uiapi_oq_job_owner_id_idx on uiapi.oq_job(owner_id);
CREATE INDEX uiapi_oq_job_profile_owner_id_idx on uiapi.oq_job_profile(owner_id);
CREATE INDEX uiapi_oq_job_status_running on uiapi.oq_job(status) WHERE status = 'running';
CREATE INDEX uiapi_output_owner_id_idx on uiapi.output(owner_id);
CREATE INDEX uiapi_upload_owner_id_idx on uiapi.upload(owner_id);

-- hzrdr indices on foreign keys
-- hazard map
CREATE INDEX hzrdr_hazard_map_output_id_idx on hzrdr.hazard_map(output_id);
CREATE INDEX hzrdr_hazard_map_data_hazard_map_id_idx on hzrdr.hazard_map_data(hazard_map_id);
-- hazard curve
CREATE INDEX hzrdr_hazard_curve_output_id_idx on hzrdr.hazard_curve(output_id);
CREATE INDEX hzrdr_hazard_curve_data_hazard_curve_id_idx on hzrdr.hazard_curve_data(hazard_curve_id);
-- gmf
CREATE INDEX hzrdr_gmf_data_output_id_idx on hzrdr.gmf_data(output_id);
-- uhs
CREATE INDEX hzrdr_uh_spectra_output_id_idx on hzrdr.uh_spectra(output_id);
CREATE INDEX hzrdr_uh_spectrum_uh_spectra_id_idx on hzrdr.uh_spectrum(uh_spectra_id);
CREATE INDEX hzrdr_uh_spectrum_data_uh_spectrum_id_idx on hzrdr.uh_spectrum_data(uh_spectrum_id);

-- riskr indexes
CREATE INDEX riskr_loss_map_output_id_idx on riskr.loss_map(output_id);
CREATE INDEX riskr_loss_map_data_loss_map_id_idx on riskr.loss_map_data(loss_map_id);
CREATE INDEX riskr_loss_curve_output_id_idx on riskr.loss_curve(output_id);
CREATE INDEX riskr_loss_curve_data_loss_curve_id_idx on riskr.loss_curve_data(loss_curve_id);
CREATE INDEX riskr_aggregate_loss_curve_data_loss_curve_id_idx on riskr.aggregate_loss_curve_data(loss_curve_id);
CREATE INDEX riskr_collapse_map_output_id_idx on riskr.collapse_map(output_id);
CREATE INDEX riskr_collapse_map_data_collapse_map_id_idx on riskr.collapse_map_data(collapse_map_id);

CREATE INDEX riskr_bcr_distribution_output_id_idx on riskr.bcr_distribution(output_id);
CREATE INDEX riskr_bcr_distribution_data_bcr_distribution_id_idx on riskr.bcr_distribution_data(bcr_distribution_id);

-- oqmif indexes
CREATE INDEX oqmif_exposure_data_site_idx ON oqmif.exposure_data USING gist(site);

-- uiapi indexes
CREATE INDEX uiapi_job2profile_oq_job_profile_id_idx on uiapi.job2profile(oq_job_profile_id);
CREATE INDEX uiapi_job2profile_job_id_idx on uiapi.job2profile(oq_job_id);
