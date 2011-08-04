/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- Update the job type constraints in uiapi.oq_job and uiapi.oq_params
-- Basically, replace 'probabilistic' with 'event_based'

ALTER TABLE uiapi.oq_job DROP CONSTRAINT job_type_value;
ALTER TABLE uiapi.oq_job ADD CONSTRAINT job_type_value
        CHECK(job_type in ('classical', 'event_based', 'deterministic'));

COMMENT ON COLUMN uiapi.oq_job.job_type IS 'One of: classical, event_based or deterministic.';

ALTER TABLE uiapi.oq_params DROP CONSTRAINT job_type_value;
ALTER TABLE uiapi.oq_params ADD CONSTRAINT job_type_value
        CHECK(job_type in ('classical', 'event_based', 'deterministic'));

COMMENT ON COLUMN uiapi.oq_params.job_type IS 'One of: classical, event_based or deterministic.';
