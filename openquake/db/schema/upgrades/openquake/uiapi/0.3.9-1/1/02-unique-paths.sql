/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- make the paths unique in uiapi.upload and uiapi.input

ALTER TABLE uiapi.input ADD CONSTRAINT unique_input_path UNIQUE (path);
ALTER TABLE uiapi.upload ADD CONSTRAINT unique_upload_path UNIQUE (path);
