/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- add a description column to the uiapi.upload table.

ALTER TABLE uiapi.upload ADD COLUMN description VARCHAR NOT NULL DEFAULT '';
