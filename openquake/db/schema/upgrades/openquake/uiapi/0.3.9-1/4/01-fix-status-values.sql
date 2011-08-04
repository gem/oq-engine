/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- Fix the status value constraints for uiapi.upload and uiapi.oq_job

ALTER TABLE uiapi.upload DROP CONSTRAINT upload_status_value;
ALTER TABLE uiapi.upload ADD CONSTRAINT upload_status_value
        CHECK(status IN ('pending', 'running', 'failed', 'succeeded'));

ALTER TABLE uiapi.oq_job DROP CONSTRAINT job_status_value;
ALTER TABLE uiapi.oq_job ADD CONSTRAINT job_status_value
        CHECK(status IN ('pending', 'running', 'failed', 'succeeded'));
