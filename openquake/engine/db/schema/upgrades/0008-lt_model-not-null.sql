-- one must create fake lt_models in the migration script
DELETE FROM hzrdr.ses_collection WHERE lt_model_id IS NULL;
ALTER TABLE hzrdr.ses_collection ALTER COLUMN lt_model_id SET NOT NULL;
