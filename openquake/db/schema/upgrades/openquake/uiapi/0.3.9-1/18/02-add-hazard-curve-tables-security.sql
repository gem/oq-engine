/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


-- uiapi.hazard_curve_{node_}data sequences
GRANT ALL ON SEQUENCE uiapi.hazard_curve_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.hazard_curve_node_data_id_seq to GROUP openquake;

-- uiapi.hazard_curve_data
GRANT SELECT ON uiapi.hazard_curve_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.hazard_curve_data TO oq_uiapi_writer;

-- uiapi.hazard_curve_node_data
GRANT SELECT ON uiapi.hazard_curve_node_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.hazard_curve_node_data TO oq_uiapi_writer;
