/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- Add a status to the uiapi.upload table.

-- Rename the 'status_value' constraint in uiapi.oq_job first.
ALTER TABLE uiapi.oq_job DROP CONSTRAINT status_value;
ALTER TABLE uiapi.oq_job ADD CONSTRAINT job_status_value
    CHECK(status IN ('created', 'in-progress', 'failed', 'succeeded'));

-- Now add the status to the uiapi.upload table.
ALTER TABLE uiapi.upload ADD COLUMN
    status VARCHAR NOT NULL DEFAULT 'created' CONSTRAINT upload_status_value
        CHECK(status IN ('created', 'in-progress', 'failed', 'succeeded'));
