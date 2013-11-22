ALTER TABLE uiapi.job_stats DROP COLUMN num_tasks;
ALTER TABLE uiapi.job_stats DROP COLUMN num_realizations;
ALTER TABLE uiapi.job_stats ADD COLUMN disk_space BIGINT;
