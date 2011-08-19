/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

ALTER TABLE uiapi.oq_job ADD COLUMN supervisor_pid INTEGER NOT NULL DEFAULT 0;

-- comments:
COMMENT ON COLUMN uiapi.oq_job.job_pid IS 'The process id (PID) of the OpenQuake engine runner process';
COMMENT ON COLUMN uiapi.oq_job.supervisor_pid IS 'The process id (PID) of the supervisor for this OpenQuake job';
