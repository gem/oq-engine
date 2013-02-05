/*
  Roles and permissions for the OpenQuake database.

    Copyright (c) 2010-2012, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/
*/


-- Please note that all OpenQuake database roles are a member of the
-- 'openquake' database group.
-- Granting certain privileges to the 'openquake' group hence applies to all
-- of our database users/roles.

GRANT USAGE ON SCHEMA admin TO GROUP openquake;
GRANT USAGE ON SCHEMA eqcat TO GROUP openquake;
GRANT USAGE ON SCHEMA hzrdi TO GROUP openquake;
GRANT USAGE ON SCHEMA hzrdr TO GROUP openquake;
GRANT USAGE ON SCHEMA oqmif TO GROUP openquake;
GRANT USAGE ON SCHEMA riski TO GROUP openquake;
GRANT USAGE ON SCHEMA riskr TO GROUP openquake;
GRANT USAGE ON SCHEMA uiapi TO GROUP openquake;
GRANT USAGE ON SCHEMA htemp to GROUP openquake;

GRANT ALL ON SEQUENCE admin.oq_user_id_seq TO oq_admin;
GRANT ALL ON SEQUENCE admin.organization_id_seq TO oq_admin;

GRANT ALL ON SEQUENCE eqcat.catalog_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE eqcat.magnitude_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE eqcat.surface_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE hzrdi.parsed_source_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.site_model_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.parsed_rupture_model_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE hzrdr.gmf_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.gmf_collection_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.gmf_set_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.gmf_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.gmf_scenario_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE hzrdr.hazard_curve_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.hazard_curve_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.hazard_map_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.uh_spectra_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.uh_spectrum_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.uh_spectrum_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.lt_realization_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.ses_collection_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.ses_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.ses_rupture_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.disagg_result_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE oqmif.exposure_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE oqmif.exposure_model_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE oqmif.occupancy_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE riskr.loss_curve_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.loss_curve_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.aggregate_loss_curve_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.loss_map_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.loss_map_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.bcr_distribution_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.bcr_distribution_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.dmg_state_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.dmg_dist_per_asset_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.dmg_dist_per_taxonomy_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.dmg_dist_total_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE uiapi.input_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.model_content_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.oq_job_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.job_phase_stats_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.job_stats_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.cnode_stats_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.hazard_calculation_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.risk_calculation_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.oq_job_profile_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.input2hcalc_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.input2rcalc_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.output_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.error_msg_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.input2job_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.src2ltsrc_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.job2profile_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE htemp.site_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE htemp.source_progress_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE htemp.hazard_curve_progress_id_seq to GROUP openquake;

GRANT SELECT ON geography_columns TO GROUP openquake;
GRANT SELECT ON geometry_columns TO GROUP openquake;
GRANT SELECT ON spatial_ref_sys TO GROUP openquake;

-- admin.oq_user
GRANT SELECT ON admin.oq_user TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON admin.oq_user TO oq_admin;

-- admin.organization
GRANT SELECT ON admin.organization TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON admin.organization TO oq_admin;

-- eqcat.catalog
GRANT SELECT ON eqcat.catalog TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON eqcat.catalog TO oq_eqcat_writer;

-- eqcat.magnitude
GRANT SELECT ON eqcat.magnitude TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON eqcat.magnitude TO oq_eqcat_writer;

-- eqcat.surface
GRANT SELECT ON eqcat.surface TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON eqcat.surface TO oq_eqcat_writer;

-- eqcat.catalog_allfields view
GRANT SELECT ON eqcat.catalog_allfields TO GROUP openquake;

-- hzrdi.parsed_source
GRANT SELECT ON hzrdi.parsed_source TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON hzrdi.parsed_source TO oq_job_init;

-- hzrdi.parsed_rupture_model
GRANT SELECT ON hzrdi.parsed_rupture_model TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON hzrdi.parsed_rupture_model TO oq_job_init;

-- hzrdi.site_model
GRANT SELECT ON hzrdi.site_model TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON hzrdi.site_model TO oq_job_init;

-- hzrdr.hazard_curve
GRANT SELECT ON hzrdr.hazard_curve TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.hazard_curve TO oq_reslt_writer;

-- hzrdr.hazard_curve_data
GRANT SELECT ON hzrdr.hazard_curve_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.hazard_curve_data TO oq_reslt_writer;

-- hzrdr.gmf_data
GRANT SELECT ON hzrdr.gmf_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.gmf_data TO oq_reslt_writer;

-- hzrdr.gmf_collection
GRANT SELECT ON hzrdr.gmf_collection TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON hzrdr.gmf_collection TO oq_reslt_writer;

-- hzrdr.gmf_set
GRANT SELECT ON hzrdr.gmf_set TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON hzrdr.gmf_set TO oq_reslt_writer;

-- hzrdr.gmf
GRANT SELECT ON hzrdr.gmf TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON hzrdr.gmf TO oq_reslt_writer;

-- hzdr.gmf_scenario
GRANT SELECT ON hzrdr.gmf_scenario TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON hzrdr.gmf_scenario TO oq_reslt_writer;

-- hzrdr.disagg_result
GRANT SELECT ON hzrdr.disagg_result TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON hzrdr.disagg_result to oq_reslt_writer;

-- hzrdr.hazard_map
GRANT SELECT ON hzrdr.hazard_map TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.hazard_map TO oq_reslt_writer;

-- hzrdr.uh_spectra
GRANT SELECT ON hzrdr.uh_spectra TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.uh_spectra TO oq_reslt_writer;

-- hzrdr.uh_spectrum
GRANT SELECT ON hzrdr.uh_spectrum TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.uh_spectrum TO oq_reslt_writer;

-- hzrdr.uh_spectrum_data
GRANT SELECT ON hzrdr.uh_spectrum_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.uh_spectrum_data TO oq_reslt_writer;

-- hzrdr.lt_realization
GRANT SELECT ON hzrdr.lt_realization TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.lt_realization TO oq_reslt_writer;

-- hzrdr.ses_collection
GRANT SELECT ON hzrdr.ses_collection TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON hzrdr.ses_collection to oq_reslt_writer;

-- hzrdr.ses
GRANT SELECT ON hzrdr.ses TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON hzrdr.ses to oq_reslt_writer;

-- hzrdr.ses_rupture
GRANT SELECT ON hzrdr.ses_rupture TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON hzrdr.ses_rupture to oq_reslt_writer;

-- oqmif.exposure_data
GRANT SELECT ON oqmif.exposure_data TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON oqmif.exposure_data TO oq_job_init;

-- oqmif.exposure_model
GRANT SELECT ON oqmif.exposure_model TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON oqmif.exposure_model TO oq_job_init;

-- oqmif.occupancy
GRANT SELECT ON oqmif.occupancy TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON oqmif.occupancy TO oq_job_init;

-- riskr.loss_curve
GRANT SELECT ON riskr.loss_curve TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.loss_curve TO oq_reslt_writer;

-- riskr.loss_curve_data
GRANT SELECT ON riskr.loss_curve_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.loss_curve_data TO oq_reslt_writer;

-- riskr.aggregate_loss_curve_data
GRANT SELECT ON riskr.aggregate_loss_curve_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.aggregate_loss_curve_data TO oq_reslt_writer;

-- riskr.loss_map
GRANT SELECT ON riskr.loss_map TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.loss_map TO oq_reslt_writer;

-- riskr.loss_map_data
GRANT SELECT ON riskr.loss_map_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.loss_map_data TO oq_reslt_writer;

-- riskr.bcr_distribution
GRANT SELECT ON riskr.bcr_distribution TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.bcr_distribution TO oq_reslt_writer;

-- riskr.bcr_distribution_data
GRANT SELECT ON riskr.bcr_distribution_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.bcr_distribution_data TO oq_reslt_writer;

-- riskr.dmg_dist_per_asset
GRANT SELECT ON riskr.dmg_state TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.dmg_state TO oq_reslt_writer;

-- riskr.dmg_dist_per_asset
GRANT SELECT ON riskr.dmg_dist_per_asset TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.dmg_dist_per_asset TO oq_reslt_writer;

-- riskr.dmg_dist_per_taxonomy
GRANT SELECT ON riskr.dmg_dist_per_taxonomy TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.dmg_dist_per_taxonomy TO oq_reslt_writer;

-- riskr.dmg_dist_total
GRANT SELECT ON riskr.dmg_dist_total TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.dmg_dist_total TO oq_reslt_writer;

-- uiapi.input
GRANT SELECT ON uiapi.input TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.input TO oq_job_init;

-- uiapi.model_content
GRANT SELECT ON uiapi.model_content TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON uiapi.model_content to oq_job_init;

-- uiapi.input2job
GRANT SELECT ON uiapi.input2job TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON uiapi.input2job TO oq_job_init;

-- uiapi.src2ltsrc
GRANT SELECT ON uiapi.src2ltsrc TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON uiapi.src2ltsrc TO oq_job_init;

-- uiapi.job2profile
GRANT SELECT ON uiapi.job2profile TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON uiapi.job2profile TO oq_job_init;

-- uiapi.oq_job
GRANT SELECT ON uiapi.oq_job TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.oq_job TO oq_job_init;

-- uiapi.job_phase_stats
-- how long are the various job phases taking?
GRANT SELECT ON uiapi.job_phase_stats TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.job_phase_stats to oq_job_init;

-- uiapi.job_stats
GRANT SELECT ON uiapi.job_stats TO GROUP openquake;
-- oq_job_init is granted write access to record job start time and other job stats at job init time
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.job_stats to oq_job_init;
-- oq_job_superv is granted write access so that the job supervisor can record job completion time
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.job_stats to oq_job_superv;

-- uiapi.hazard_calculation
GRANT SELECT ON uiapi.hazard_calculation TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.hazard_calculation TO oq_job_init;

-- uiapi.input2hcalc
GRANT SELECT ON uiapi.input2hcalc TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON uiapi.input2hcalc TO oq_job_init;

-- uiapi.risk_calculation
GRANT SELECT ON uiapi.risk_calculation TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON uiapi.risk_calculation TO oq_job_init;

-- uiapi.input2rcalc
GRANT SELECT ON uiapi.input2rcalc TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON uiapi.input2rcalc TO oq_job_init;

-- uiapi.cnode_stats
-- what nodes became available/unavailable at what time?
GRANT SELECT ON uiapi.cnode_stats TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON uiapi.cnode_stats to oq_job_superv;

-- uiapi.oq_job_profile
GRANT SELECT ON uiapi.oq_job_profile TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.oq_job_profile TO oq_job_init;

-- uiapi.output
GRANT SELECT ON uiapi.output TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON uiapi.output TO oq_reslt_writer;

-- uiapi.error_msg
GRANT SELECT ON uiapi.error_msg TO openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.error_msg TO oq_job_superv;

-- htemp.site_data
GRANT SELECT ON htemp.site_data TO openquake;
GRANT SELECT,INSERT,DELETE ON htemp.site_data TO oq_reslt_writer;

-- htemp.source_progress
GRANT SELECT ON htemp.source_progress TO openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON htemp.source_progress TO oq_reslt_writer;

-- htemp.hazard_curve_progress
GRANT SELECT ON htemp.hazard_curve_progress TO openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON htemp.hazard_curve_progress TO oq_reslt_writer;
