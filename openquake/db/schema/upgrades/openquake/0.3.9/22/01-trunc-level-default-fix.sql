/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


-- Make sure we have a valid truncation_level value for all rows.
UPDATE uiapi.oq_params SET truncation_level = 3.0 WHERE truncation_level IS NULL OR truncation_level = 0.0;

ALTER TABLE uiapi.oq_params ALTER COLUMN truncation_level SET DEFAULT 3.0;
