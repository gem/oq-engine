/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- pshai.source and pshai.rupture need to be associated with uiapi.input
-- This patch adds the needed foreign keys.

ALTER TABLE pshai.rupture ADD COLUMN input_id INTEGER;
ALTER TABLE pshai.source ADD COLUMN input_id INTEGER;

ALTER TABLE pshai.source ADD CONSTRAINT pshai_source_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE RESTRICT;

ALTER TABLE pshai.rupture ADD CONSTRAINT pshai_rupture_input_fk
FOREIGN KEY (input_id) REFERENCES uiapi.input(id) ON DELETE RESTRICT;
