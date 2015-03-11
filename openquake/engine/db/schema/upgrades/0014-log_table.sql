CREATE TABLE uiapi.log (
   id SERIAL PRIMARY KEY,
   job_id INTEGER NOT NULL REFERENCES uiapi.oq_job (id) ON DELETE CASCADE,
   timestamp TIMESTAMP NOT NULL,
   level TEXT NOT NULL,
   process TEXT NOT NULL,
   message TEXT NOT NULL
) TABLESPACE uiapi_ts;

GRANT SELECT,INSERT ON uiapi.log TO oq_job_init;
GRANT USAGE ON uiapi.log_id_seq TO oq_job_init;

COMMENT ON TABLE uiapi.log IS 'Log data for the calculations';
COMMENT ON COLUMN uiapi.log.job_id IS 'The ID of the job';
COMMENT ON COLUMN uiapi.log.timestamp IS 'The timestamp of the log';
COMMENT ON COLUMN uiapi.log.level IS 'The log level';
COMMENT ON COLUMN uiapi.log.process IS 'The process ID as a string';
COMMENT ON COLUMN uiapi.log.message IS 'The log message';

