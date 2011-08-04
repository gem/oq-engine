/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


GRANT ALL ON SEQUENCE uiapi.gmf_data_id_seq to GROUP openquake;

GRANT SELECT ON uiapi.gmf_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.gmf_data TO oq_uiapi_writer;
