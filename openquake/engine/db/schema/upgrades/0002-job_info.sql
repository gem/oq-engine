CREATE TABLE uiapi.job_info(
id SERIAL PRIMARY KEY,
oq_job_id INTEGER NOT NULL REFERENCES uiapi.oq_job(id),
parent_job_id INTEGER REFERENCES uiapi.oq_job(id),
num_sites INTEGER NOT NULL,
num_realizations INTEGER NOT NULL,
num_imts INTEGER NOT NULL,
num_levels FLOAT NOT NULL,
input_weight FLOAT NOT NULL,
output_weight FLOAT NOT NULL
) TABLESPACE uiapi_ts;

GRANT SELECT,INSERT ON uiapi.job_info TO oq_job_init;
GRANT USAGE ON uiapi.job_info_id_seq TO oq_job_init;

COMMENT ON TABLE uiapi.job_info IS 'Information about a given job';
COMMENT ON COLUMN uiapi.job_info.num_sites IS 'The number of affected sites';
COMMENT ON COLUMN uiapi.job_info.num_realizations IS 'The number of realizations (possibly overestimated)';
COMMENT ON COLUMN uiapi.job_info.num_imts IS 'The number of IMTs in the job.ini';
COMMENT ON COLUMN uiapi.job_info.num_levels IS 'The average number of hazard levels per IMT';
COMMENT ON COLUMN uiapi.job_info.input_weight IS 'The weight of the relevant sources in the source model';
COMMENT ON COLUMN uiapi.job_info.output_weight IS 'The weight of the expected output, proportional to num_sites * num_realizations * num_imts';
