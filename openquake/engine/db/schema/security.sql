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
GRANT USAGE ON SCHEMA htemp TO GROUP openquake;
GRANT USAGE ON SCHEMA hzrdi TO GROUP openquake;
GRANT USAGE ON SCHEMA hzrdr TO GROUP openquake;
GRANT USAGE ON SCHEMA oqmif TO GROUP openquake;
GRANT USAGE ON SCHEMA riski TO GROUP openquake;
GRANT USAGE ON SCHEMA riskr TO GROUP openquake;
GRANT USAGE ON SCHEMA uiapi TO GROUP openquake;

GRANT ALL ON ALL SEQUENCES IN SCHEMA admin TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA htemp TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA hzrdi TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA hzrdr TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA oqmif TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA riski TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA riskr TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA uiapi TO GROUP openquake;

-- Users in the `openquake` group have read access to everything
GRANT SELECT ON ALL TABLES IN SCHEMA admin TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA htemp TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA hzrdi TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA hzrdr TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA oqmif TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA riski TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA riskr TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA uiapi TO GROUP openquake;
GRANT SELECT ON geography_columns          TO GROUP openquake;
GRANT SELECT ON geometry_columns           TO GROUP openquake;
GRANT SELECT ON spatial_ref_sys            TO GROUP openquake;

-- `oq_admin` has full SELECT/INSERT/UPDATE/DELETE access to all tables.
-- In fact, `oq_admin` is the only user that can delete records,
-- with the exception the `htemp` schema space. See below.
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA admin TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA htemp TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA hzrdi TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA hzrdr TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA oqmif TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA riski TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA riskr TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA uiapi TO oq_admin;

----------------------------------------------
-- Specific permissions for individual tables:
----------------------------------------------
-- admin schema
GRANT SELECT,INSERT,UPDATE ON admin.oq_user      TO oq_admin;
GRANT SELECT,INSERT,UPDATE ON admin.organization TO oq_admin;

-- htemp schema
GRANT SELECT,INSERT,DELETE        ON htemp.site_data             TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON htemp.source_progress       TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON htemp.hazard_curve_progress TO oq_reslt_writer;

-- hzrdi schema
GRANT SELECT,INSERT ON hzrdi.parsed_source        TO oq_job_init;
GRANT SELECT,INSERT ON hzrdi.parsed_rupture_model TO oq_job_init;
GRANT SELECT,INSERT ON hzrdi.site_model           TO oq_job_init;

-- hzrdr schema
GRANT SELECT,INSERT        ON hzrdr.hazard_curve      TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON hzrdr.hazard_curve_data TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON hzrdr.gmf_data          TO oq_reslt_writer;
GRANT SELECT,INSERT        ON hzrdr.gmf_collection    TO oq_reslt_writer;
GRANT SELECT,INSERT        ON hzrdr.gmf_set           TO oq_reslt_writer;
GRANT SELECT,INSERT        ON hzrdr.gmf               TO oq_reslt_writer;
GRANT SELECT,INSERT        ON hzrdr.gmf_scenario      TO oq_reslt_writer;
GRANT SELECT,INSERT        ON hzrdr.gmf_agg           TO oq_reslt_writer;
GRANT SELECT,INSERT        ON hzrdr.disagg_result     TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON hzrdr.hazard_map        TO oq_reslt_writer;
GRANT SELECT,INSERT        ON hzrdr.uhs               TO oq_reslt_writer;
GRANT SELECT,INSERT        ON hzrdr.uhs_data          TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON hzrdr.lt_realization    TO oq_reslt_writer;
GRANT SELECT,INSERT        ON hzrdr.ses_collection    TO oq_reslt_writer;
GRANT SELECT,INSERT        ON hzrdr.ses               TO oq_reslt_writer;
GRANT SELECT,INSERT        ON hzrdr.ses_rupture       TO oq_reslt_writer;

-- oqmif schema
GRANT SELECT,INSERT        ON oqmif.exposure_data    TO oq_job_init;
GRANT SELECT,INSERT        ON oqmif.exposure_model   TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON oqmif.occupancy        TO oq_job_init;

-- riskr schema
GRANT SELECT,INSERT,UPDATE ON riskr.loss_curve                TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_curve_data           TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON riskr.aggregate_loss_curve_data TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_map                  TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_map_data             TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_fraction             TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_fraction_data        TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON riskr.aggregate_loss            TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON riskr.bcr_distribution          TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON riskr.bcr_distribution_data     TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON riskr.dmg_state                 TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON riskr.dmg_dist_per_asset        TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON riskr.dmg_dist_per_taxonomy     TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON riskr.dmg_dist_total            TO oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON riskr.event_loss                TO oq_reslt_writer;

-- uiapi schema
GRANT SELECT,INSERT,UPDATE ON uiapi.input              TO oq_job_init;
GRANT SELECT,INSERT        ON uiapi.model_content      TO oq_job_init;
GRANT SELECT,INSERT        ON uiapi.input2job          TO oq_job_init;
GRANT SELECT,INSERT        ON uiapi.src2ltsrc          TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON uiapi.oq_job             TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON uiapi.job_phase_stats    TO oq_job_init;
-- oq_job_init is granted write access to record job start time and other job stats at job init time
GRANT SELECT,INSERT,UPDATE ON uiapi.job_stats          TO oq_job_init;
-- oq_job_superv is granted write access so that the job supervisor can record job completion time
GRANT SELECT,INSERT,UPDATE ON uiapi.job_stats          TO oq_job_superv;
GRANT SELECT,INSERT,UPDATE ON uiapi.hazard_calculation TO oq_job_init;
GRANT SELECT,INSERT        ON uiapi.input2hcalc        TO oq_job_init;
GRANT SELECT,INSERT        ON uiapi.risk_calculation   TO oq_job_init;
GRANT SELECT,INSERT        ON uiapi.input2rcalc        TO oq_job_init;
-- what nodes became available/unavailable at what time?
GRANT SELECT,INSERT,UPDATE ON uiapi.cnode_stats        TO oq_job_superv;
GRANT SELECT,INSERT,UPDATE ON uiapi.output             TO oq_reslt_writer;
GRANT SELECT,INSERT        ON uiapi.error_msg          TO oq_job_superv;
GRANT SELECT,INSERT        ON uiapi.performance        TO oq_job_init;
