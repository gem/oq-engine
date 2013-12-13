ALTER TABLE hzrdr.ses_collection DROP COLUMN lt_realization_id;
ALTER TABLE hzrdr.ses_collection ADD COLUMN ordinal INTEGER NOT NULL DEFAULT 0;
ALTER TABLE hzrdr.ses_collection ADD COLUMN sm_path TEXT NOT NULL;
ALTER TABLE hzrdr.ses_collection ADD COLUMN sm_lt_path TEXT[] NOT NULL;
ALTER TABLE hzrdr.ses_collection ADD COLUMN weight FLOAT;

ALTER TABLE hzrdr.ses ALTER COLUMN ordinal SET NOT NULL;

ALTER TABLE hzrdr.lt_realization DROP COLUMN is_complete;
ALTER TABLE hzrdr.lt_realization DROP COLUMN total_items;
ALTER TABLE hzrdr.lt_realization DROP COLUMN completed_items;

ALTER TABLE hzrdr.gmf_data RENAME ses_id TO task_no;

UPDATE hzrdr.gmf_data SET task_no=0 WHERE task_no IS NULL;
ALTER TABLE hzrdr.gmf_data ALTER COLUMN task_no SET NOT NULL;
