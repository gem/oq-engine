ALTER TABLE hzrdr.ses_collection DROP COLUMN lt_realization_id;
ALTER TABLE hzrdr.ses_collection ADD COLUMN sm_lt_path TEXT[] NOT NULL;

ALTER TABLE hzrdr.ses ALTER COLUMN ordinal SET NOT NULL;
