/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

BEGIN;
ALTER TABLE hzrdr.hazard_curve_node_data
    DROP CONSTRAINT hzrdr_hazard_curve_node_data_output_fk;

ALTER TABLE hzrdr.hazard_curve_node_data
    RENAME TO hazard_curve_data;
ALTER INDEX hzrdr.hzrdr_hazard_curve_node_data_hazard_curve_id_idx
    RENAME TO hzrdr_hazard_curve_data_hazard_curve_id_idx;

ALTER TABLE hzrdr.hazard_curve_data
    ADD CONSTRAINT hzrdr_hazard_curve_data_hazard_curve_fk
    FOREIGN KEY (hazard_curve_id) REFERENCES hzrdr.hazard_curve(id)
        ON DELETE CASCADE;
COMMIT;
