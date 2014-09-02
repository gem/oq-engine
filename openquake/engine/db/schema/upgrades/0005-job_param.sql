CREATE TABLE uiapi.job_param (
   id SERIAL PRIMARY KEY,
   job_id INTEGER NOT NULL REFERENCES uiapi.oq_job (id) ON DELETE CASCADE,
   name TEXT NOT NULL,
   value TEXT NOT NULL,
   UNIQUE (job_id, name)
) TABLESPACE uiapi_ts;

GRANT SELECT,INSERT ON uiapi.job_param TO oq_job_init;
GRANT USAGE ON uiapi.job_param_id_seq TO oq_job_init;

COMMENT ON TABLE uiapi.job_param IS 'Associations between a job and its parameters';
COMMENT ON COLUMN uiapi.job_param.job_id IS 'The ID of the job';
COMMENT ON COLUMN uiapi.job_param.name IS 'The name of the parameter';
COMMENT ON COLUMN uiapi.job_param.value IS 'The value of the parameter as a Python object representation';
