DELETE FROM uiapi.output WHERE oq_job_id IS NULL;

ALTER TABLE uiapi.output ALTER COLUMN oq_job_id SET NOT NULL;
