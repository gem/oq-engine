/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- Add a 'job_pid' column to uiapi.upload and uiapi.oq_job

ALTER TABLE uiapi.upload ADD COLUMN job_pid INTEGER NOT NULL DEFAULT 0;
ALTER TABLE uiapi.oq_job ALTER COLUMN duration SET DEFAULT 0;
ALTER TABLE uiapi.oq_job ADD COLUMN job_pid INTEGER NOT NULL DEFAULT 0;
