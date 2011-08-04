/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- Grant read/write permissions on the pshai tables to role oq_uiapi_writer.

GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.complex_fault TO oq_uiapi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.fault_edge TO oq_uiapi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.focal_mechanism TO oq_uiapi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.mfd_evd TO oq_uiapi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.mfd_tgr TO oq_uiapi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.r_depth_distr TO oq_uiapi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.r_rate_mdl TO oq_uiapi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.rupture TO oq_uiapi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.simple_fault TO oq_uiapi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.source TO oq_uiapi_writer;
