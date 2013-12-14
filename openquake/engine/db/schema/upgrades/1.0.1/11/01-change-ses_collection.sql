ALTER TABLE hzrdr.ses ALTER COLUMN ordinal SET NOT NULL;

ALTER TABLE hzrdr.lt_realization DROP COLUMN is_complete;
ALTER TABLE hzrdr.lt_realization DROP COLUMN total_items;
ALTER TABLE hzrdr.lt_realization DROP COLUMN completed_items;

ALTER TABLE uiapi.job_stats ADD COLUMN num_sources INTEGER[];
