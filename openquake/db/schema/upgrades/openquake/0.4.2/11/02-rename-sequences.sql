/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


-- Rename sequences
ALTER SEQUENCE hzrdr.hazard_curve_data_id_seq RENAME TO hazard_curve_id_seq;
ALTER SEQUENCE hzrdr.hazard_curve_node_data_id_seq RENAME TO hazard_curve_data_id_seq;

-- Rename primary keys
ALTER TABLE hzrdr.hazard_curve_data_pkey RENAME TO hazard_curve_pkey;
ALTER TABLE hzrdr.hazard_curve_node_data_pkey RENAME TO hazard_curve_data_pkey;

-- Rename constraints
ALTER TABLE riski.vulnerability_data_vulnerability_model_id_key RENAME TO
    vulnerability_function_vulnerability_model_id_key;
