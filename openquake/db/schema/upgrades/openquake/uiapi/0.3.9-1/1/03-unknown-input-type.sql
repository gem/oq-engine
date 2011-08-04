/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- allow for an unknown input type.

ALTER TABLE uiapi.input DROP CONSTRAINT input_type_value;
ALTER TABLE uiapi.input ADD CONSTRAINT input_type_value CHECK(input_type IN ('unknown', 'source', 'ltree', 'exposure', 'vulnerability'));
