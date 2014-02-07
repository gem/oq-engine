ALTER TABLE hzrdr.ses_collection ADD COLUMN lt_realizations INTEGER[];
ALTER TABLE hzrdr.ses_collection ADD COLUMN ordinal INTEGER;

UPDATE hzrdr.ses_collection
SET lt_realization_ids=ARRAY[lt_realization_id], ordinal=lt_realization_id;

ALTER TABLE hzrdr.ses_collection ALTER COLUMN lt_realization_ids NOT NULL;
ALTER TABLE hzrdr.ses_collection ALTER COLUMN ordinal NOT NULL;

ALTER TABLE hzrdr.ses_collection DROP COLUMN lt_realization_id;
