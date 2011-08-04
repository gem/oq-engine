/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- oq_job.path is nullable no matter what the status (path is not filled, and
-- not used, by bin/openquake)

ALTER TABLE uiapi.oq_job DROP CONSTRAINT job_path_value;
