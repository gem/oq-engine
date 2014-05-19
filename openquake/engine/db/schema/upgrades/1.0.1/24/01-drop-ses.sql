DROP TABLE hzrdr.ses; -- obsolete

ALTER TABLE hzrdr.ses_collection ALTER COLUMN lt_model_id DROP NOT NULL;
