/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- Replace the 'ltree' input type contraint with two options: 'lt_source' and 'lt_gmpe'

ALTER TABLE uiapi.input DROP CONSTRAINT input_type_value;
ALTER TABLE uiapi.input ADD CONSTRAINT input_type_value CHECK(input_type IN ('unknown', 'source', 'lt_source', 'lt_gmpe', 'exposure', 'vulnerability'));

COMMENT ON COLUMN uiapi.input.input_type IS 'Input file type, one of:
    - source model file (source)
    - source logic tree (lt_source)
    - GMPE logic tree (lt_gmpe)
    - exposure file (exposure)
    - vulnerability file (vulnerability)';
