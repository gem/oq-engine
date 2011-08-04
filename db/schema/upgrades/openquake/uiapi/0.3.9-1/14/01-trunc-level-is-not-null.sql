/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


-- Drop the unneeded constraint.
ALTER TABLE uiapi.oq_params DROP CONSTRAINT truncation_level_is_set;

-- Make sure we have a truncation_level value for all rows.
UPDATE uiapi.oq_params SET truncation_level = 0.0 WHERE truncation_level IS NULL;

ALTER TABLE uiapi.oq_params ALTER COLUMN truncation_level SET DEFAULT 0.0;
ALTER TABLE uiapi.oq_params ALTER COLUMN truncation_level SET NOT NULL;
