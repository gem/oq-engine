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

GRANT ALL ON SEQUENCE oqmif.exposure_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE oqmif.exposure_model_id_seq to GROUP openquake;

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

GRANT ALL ON SEQUENCE uiapi.input_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.oq_calculation_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.calc_stats_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.oq_job_profile_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.output_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.upload_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.input_set_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.error_msg_id_seq to GROUP openquake;

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
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.complex_fault TO oq_calculation_init;

-- hzrdi.fault_edge
GRANT SELECT ON hzrdi.fault_edge TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.fault_edge TO oq_calculation_init;

-- hzrdi.focal_mechanism
GRANT SELECT ON hzrdi.focal_mechanism TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.focal_mechanism TO oq_calculation_init;

-- hzrdi.mfd_evd
GRANT SELECT ON hzrdi.mfd_evd TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.mfd_evd TO oq_calculation_init;

-- hzrdi.mfd_tgr
GRANT SELECT ON hzrdi.mfd_tgr TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.mfd_tgr TO oq_calculation_init;

-- hzrdi.r_depth_distr
GRANT SELECT ON hzrdi.r_depth_distr TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.r_depth_distr TO oq_calculation_init;

-- hzrdi.r_rate_mdl
GRANT SELECT ON hzrdi.r_rate_mdl TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.r_rate_mdl TO oq_calculation_init;

-- hzrdi.rupture
GRANT SELECT ON hzrdi.rupture TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.rupture TO oq_calculation_init;

-- hzrdi.simple_fault
GRANT SELECT ON hzrdi.simple_fault TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.simple_fault TO oq_calculation_init;

-- hzrdi.source
GRANT SELECT ON hzrdi.source TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.source TO oq_calculation_init;

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

-- oqmif.exposure_data
GRANT SELECT ON oqmif.exposure_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON oqmif.exposure_data TO oq_ged4gem;

-- oqmif.exposure_model
GRANT SELECT ON oqmif.exposure_model TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON oqmif.exposure_model TO oq_ged4gem;

-- riski.vulnerability_function
GRANT SELECT ON riski.vulnerability_function TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riski.vulnerability_function TO oq_calculation_init;

-- riski.vulnerability_model
GRANT SELECT ON riski.vulnerability_model TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riski.vulnerability_model TO oq_calculation_init;

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

-- uiapi.input
GRANT SELECT ON uiapi.input TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.input TO oq_calculation_init;

-- uiapi.oq_calculation
GRANT SELECT ON uiapi.oq_calculation TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON uiapi.oq_calculation TO oq_calculation_init;

-- uiapi.calc_stats
GRANT SELECT ON uiapi.calc_stats TO GROUP openquake;
-- oq_calculation_init is granted write access to record job start time and other job stats at job init time
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.calc_stats to oq_calculation_init;
-- oq_calculation_superv is granted write access so that the job supervisor can record job completion time
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.calc_stats to oq_calculation_superv;

-- uiapi.oq_job_profile
GRANT SELECT ON uiapi.oq_job_profile TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON uiapi.oq_job_profile TO oq_calculation_init;

-- uiapi.output
GRANT SELECT ON uiapi.output TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON uiapi.output TO oq_reslt_writer;

-- uiapi.input_set
GRANT SELECT ON uiapi.input_set TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.input_set TO oq_calculation_init;

-- uiapi.upload
GRANT SELECT ON uiapi.upload TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.upload TO oq_calculation_init;

-- uiapi.error_msg
GRANT SELECT ON uiapi.error_msg TO openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.error_msg TO oq_calculation_superv;
