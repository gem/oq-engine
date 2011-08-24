/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

REVOKE ALL PRIVILEGES ON hzrdi.complex_fault FROM oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.complex_fault TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON hzrdi.fault_edge FROM oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.fault_edge TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON hzrdi.focal_mechanism FROM oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.focal_mechanism TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON hzrdi.mfd_evd FROM oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.mfd_evd TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON hzrdi.mfd_tgr FROM oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.mfd_tgr TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON hzrdi.r_depth_distr FROM oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.r_depth_distr TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON hzrdi.r_rate_mdl FROM oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.r_rate_mdl TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON hzrdi.rupture FROM oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.rupture TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON hzrdi.simple_fault FROM oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.simple_fault TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON hzrdi.source FROM oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.source TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON riski.vulnerability_function FROM oq_riski_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON riski.vulnerability_function TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON riski.vulnerability_model FROM oq_riski_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON riski.vulnerability_model TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON uiapi.input FROM oq_uiapi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.input TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON uiapi.oq_job FROM oq_uiapi_writer;
REVOKE ALL PRIVILEGES ON uiapi.oq_job FROM oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON uiapi.oq_job TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON uiapi.oq_params FROM oq_uiapi_writer;
REVOKE ALL PRIVILEGES ON uiapi.oq_params FROM oq_reslt_writer;
GRANT SELECT,INSERT,UPDATE ON uiapi.oq_params TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON uiapi.output FROM oq_uiapi_writer;
 
REVOKE ALL PRIVILEGES ON uiapi.upload FROM oq_uiapi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.upload TO oq_job_init;
 
REVOKE ALL PRIVILEGES ON uiapi.error_msg FROM oq_uiapi_reader;
REVOKE ALL PRIVILEGES ON uiapi.error_msg FROM oq_uiapi_writer;
GRANT SELECT ON uiapi.error_msg TO openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.error_msg TO oq_job_superv;
