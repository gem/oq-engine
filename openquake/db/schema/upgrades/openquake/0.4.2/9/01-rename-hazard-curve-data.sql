/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

BEGIN;
ALTER TABLE hzrdr.hazard_curve_data
    DROP CONSTRAINT hzrdr_hazard_curve_data_output_fk;

ALTER TABLE hzrdr.hazard_curve_data
    RENAME TO hazard_curve;
ALTER TABLE hzrdr.hazard_curve_node_data
    RENAME COLUMN hazard_curve_data_id TO hazard_curve_id;
ALTER INDEX hzrdr.hzrdr_hazard_curve_data_output_id_idx
    RENAME TO hzrdr_hazard_curve_output_id_idx;
ALTER INDEX hzrdr.hzrdr_hazard_curve_node_data_hazard_curve_data_id_idx
    RENAME TO hzrdr_hazard_curve_node_data_hazard_curve_id_idx;

ALTER TABLE hzrdr.hazard_curve
    ADD CONSTRAINT hzrdr_hazard_curve_output_fk
    FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;
COMMIT;
