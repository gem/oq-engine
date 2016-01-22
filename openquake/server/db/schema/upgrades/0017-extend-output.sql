ALTER TABLE uiapi.oq_job ADD COLUMN ds_calc_dir TEXT;

COMMENT ON COLUMN uiapi.oq_job.ds_calc_dir IS 'datastore path';

ALTER TABLE uiapi.output ADD COLUMN ds_key TEXT;

COMMENT ON COLUMN uiapi.output.ds_key IS 'datastore key';
