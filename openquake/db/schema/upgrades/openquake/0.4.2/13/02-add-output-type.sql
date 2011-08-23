/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


-- constraint
BEGIN;
ALTER TABLE uiapi.output DROP CONSTRAINT output_type_value;
ALTER TABLE uiapi.output ADD CONSTRAINT output_type_value
        CHECK(output_type IN ('unknown', 'hazard_curve', 'hazard_map',
            'gmf', 'loss_curve', 'loss_map', 'collapse_map'));
COMMIT;


-- comment
COMMENT ON COLUMN uiapi.output.output_type IS 'Output type, one of:
    - unknown
    - hazard_curve
    - hazard_map
    - gmf
    - loss_curve
    - loss_map
    - collapse_map';
