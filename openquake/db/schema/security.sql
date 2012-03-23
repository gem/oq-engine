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

GRANT ALL ON SEQUENCE admin.oq_user_id_seq TO oq_admin;
GRANT ALL ON SEQUENCE admin.organization_id_seq TO oq_admin;

GRANT ALL ON SEQUENCE eqcat.catalog_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE eqcat.magnitude_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE eqcat.surface_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE hzrdi.complex_fault_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.fault_edge_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.focal_mechanism_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.mfd_evd_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.mfd_tgr_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.r_depth_distr_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.r_rate_mdl_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.rupture_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.simple_fault_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.source_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE hzrdr.gmf_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.hazard_curve_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.hazard_curve_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.hazard_map_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.hazard_map_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.uh_spectra_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.uh_spectrum_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdr.uh_spectrum_data_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE oqmif.exposure_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE oqmif.exposure_model_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE oqmif.occupancy_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE riski.ffc_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riski.ffd_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riski.fragility_model_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riski.vulnerability_function_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riski.vulnerability_model_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE riskr.loss_curve_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.loss_curve_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.aggregate_loss_curve_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.loss_map_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.loss_map_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.collapse_map_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.collapse_map_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.bcr_distribution_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.bcr_distribution_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.dmg_dist_per_asset_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.dmg_dist_per_asset_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.dmg_dist_per_taxonomy_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.dmg_dist_per_taxonomy_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.dmg_dist_total_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.dmg_dist_total_data_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE uiapi.input_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.oq_job_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.job_stats_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.oq_job_profile_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.output_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.upload_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.error_msg_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.input2job_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.input2upload_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.job2profile_id_seq to GROUP openquake;

GRANT SELECT ON geography_columns TO GROUP openquake;
GRANT SELECT ON geometry_columns TO GROUP openquake;

GRANT SELECT ON hzrdi.complex_source TO GROUP openquake;
GRANT SELECT ON hzrdi.simple_source TO GROUP openquake;
GRANT SELECT ON hzrdi.complex_rupture TO GROUP openquake;
GRANT SELECT ON hzrdi.simple_rupture TO GROUP openquake;

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

-- hzrdi.complex_fault
GRANT SELECT ON hzrdi.complex_fault TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.complex_fault TO oq_job_init;

-- hzrdi.fault_edge
GRANT SELECT ON hzrdi.fault_edge TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.fault_edge TO oq_job_init;

-- hzrdi.focal_mechanism
GRANT SELECT ON hzrdi.focal_mechanism TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.focal_mechanism TO oq_job_init;

-- hzrdi.mfd_evd
GRANT SELECT ON hzrdi.mfd_evd TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.mfd_evd TO oq_job_init;

-- hzrdi.mfd_tgr
GRANT SELECT ON hzrdi.mfd_tgr TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.mfd_tgr TO oq_job_init;

-- hzrdi.r_depth_distr
GRANT SELECT ON hzrdi.r_depth_distr TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.r_depth_distr TO oq_job_init;

-- hzrdi.r_rate_mdl
GRANT SELECT ON hzrdi.r_rate_mdl TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.r_rate_mdl TO oq_job_init;

-- hzrdi.rupture
GRANT SELECT ON hzrdi.rupture TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.rupture TO oq_job_init;

-- hzrdi.simple_fault
GRANT SELECT ON hzrdi.simple_fault TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.simple_fault TO oq_job_init;

-- hzrdi.source
GRANT SELECT ON hzrdi.source TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.source TO oq_job_init;

-- hzrdr.hazard_curve
GRANT SELECT ON hzrdr.hazard_curve TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.hazard_curve TO oq_reslt_writer;

-- hzrdr.hazard_curve_data
GRANT SELECT ON hzrdr.hazard_curve_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.hazard_curve_data TO oq_reslt_writer;

-- hzrdr.gmf_data
GRANT SELECT ON hzrdr.gmf_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.gmf_data TO oq_reslt_writer;

-- hzrdr.hazard_map
GRANT SELECT ON hzrdr.hazard_map TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.hazard_map TO oq_reslt_writer;

-- hzrdr.hazard_map_data
GRANT SELECT ON hzrdr.hazard_map_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.hazard_map_data TO oq_reslt_writer;

-- hzrdr.uh_spectra
GRANT SELECT ON hzrdr.uh_spectra TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.uh_spectra TO oq_reslt_writer;

-- hzrdr.uh_spectrum
GRANT SELECT ON hzrdr.uh_spectrum TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.uh_spectrum TO oq_reslt_writer;

-- hzrdr.uh_spectrum_data
GRANT SELECT ON hzrdr.uh_spectrum_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdr.uh_spectrum_data TO oq_reslt_writer;

-- oqmif.exposure_data
GRANT SELECT ON oqmif.exposure_data TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON oqmif.exposure_data TO oq_ged4gem;
GRANT SELECT,INSERT,DELETE ON oqmif.exposure_data TO oq_job_init;

-- oqmif.exposure_model
GRANT SELECT ON oqmif.exposure_model TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON oqmif.exposure_model TO oq_ged4gem;
GRANT SELECT,INSERT,DELETE ON oqmif.exposure_model TO oq_job_init;

-- oqmif.occupancy
GRANT SELECT ON oqmif.occupancy TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON oqmif.occupancy TO oq_ged4gem;
GRANT SELECT,INSERT,UPDATE,DELETE ON oqmif.occupancy TO oq_job_init;

-- riski.ffc
GRANT SELECT ON riski.ffc TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON riski.ffc TO oq_job_init;

-- riski.ffd
GRANT SELECT ON riski.ffd TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON riski.ffd TO oq_job_init;

-- riski.fragility_model
GRANT SELECT ON riski.fragility_model TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON riski.fragility_model TO oq_job_init;

-- riski.vulnerability_function
GRANT SELECT ON riski.vulnerability_function TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riski.vulnerability_function TO oq_job_init;

-- riski.vulnerability_model
GRANT SELECT ON riski.vulnerability_model TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riski.vulnerability_model TO oq_job_init;

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

-- riskr.collapse_map
GRANT SELECT ON riskr.collapse_map TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.collapse_map TO oq_reslt_writer;

-- riskr.collapse_map_data
GRANT SELECT ON riskr.collapse_map_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.collapse_map_data TO oq_reslt_writer;

-- riskr.bcr_distribution
GRANT SELECT ON riskr.bcr_distribution TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.bcr_distribution TO oq_reslt_writer;

-- riskr.bcr_distribution_data
GRANT SELECT ON riskr.bcr_distribution_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.bcr_distribution_data TO oq_reslt_writer;

-- riskr.dmg_dist_per_asset
GRANT SELECT ON riskr.dmg_dist_per_asset TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.dmg_dist_per_asset TO oq_reslt_writer;

-- riskr.dmg_dist_per_asset_data
GRANT SELECT ON riskr.dmg_dist_per_asset_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.dmg_dist_per_asset_data TO oq_reslt_writer;

-- riskr.dmg_dist_per_taxonomy
GRANT SELECT ON riskr.dmg_dist_per_taxonomy TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.dmg_dist_per_taxonomy TO oq_reslt_writer;

-- riskr.dmg_dist_per_taxonomy_data
GRANT SELECT ON riskr.dmg_dist_per_taxonomy_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.dmg_dist_per_taxonomy_data TO oq_reslt_writer;

-- riskr.dmg_dist_total
GRANT SELECT ON riskr.dmg_dist_total TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.dmg_dist_total TO oq_reslt_writer;

-- riskr.dmg_dist_total_data
GRANT SELECT ON riskr.dmg_dist_total_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.dmg_dist_total_data TO oq_reslt_writer;

-- uiapi.input
GRANT SELECT ON uiapi.input TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.input TO oq_job_init;

-- uiapi.input2job
GRANT SELECT ON uiapi.input2job TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON uiapi.input2job TO oq_job_init;

-- uiapi.input2upload
GRANT SELECT ON uiapi.input2upload TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON uiapi.input2upload TO oq_job_init;

-- uiapi.job2profile
GRANT SELECT ON uiapi.job2profile TO GROUP openquake;
GRANT SELECT,INSERT,DELETE ON uiapi.job2profile TO oq_job_init;

-- uiapi.oq_job
GRANT SELECT ON uiapi.oq_job TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.oq_job TO oq_job_init;

-- uiapi.job_stats
GRANT SELECT ON uiapi.job_stats TO GROUP openquake;
-- oq_job_init is granted write access to record job start time and other job stats at job init time
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.job_stats to oq_job_init;
-- oq_job_superv is granted write access so that the job supervisor can record job completion time
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.job_stats to oq_job_superv;

-- uiapi.oq_job_profile
GRANT SELECT ON uiapi.oq_job_profile TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.oq_job_profile TO oq_job_init;

-- uiapi.output
GRANT SELECT ON uiapi.output TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON uiapi.output TO oq_reslt_writer;

-- uiapi.upload
GRANT SELECT ON uiapi.upload TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.upload TO oq_job_init;

-- uiapi.error_msg
GRANT SELECT ON uiapi.error_msg TO openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.error_msg TO oq_job_superv;
