/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- Fix wrong column in truncation_type_value constraint

ALTER TABLE uiapi.oq_params DROP CONSTRAINT truncation_type_value;
ALTER TABLE uiapi.oq_params ADD CONSTRAINT truncation_type_value CHECK(truncation_type IN ('none', '1-sided', '2-sided'));
