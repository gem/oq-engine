/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- The uiapi.oq_job.path column should be optional as long as the job has not
-- been started.

ALTER TABLE uiapi.oq_job ALTER COLUMN path DROP NOT NULL;
ALTER TABLE uiapi.oq_job ADD CONSTRAINT job_path_value
    CHECK(status IN ('running', 'failed', 'succeeded') AND path IS NOT NULL);
