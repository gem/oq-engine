ALTER TABLE hzrdr.source_info ALTER COLUMN occ_ruptures DROP NOT NULL;
ALTER TABLE hzrdr.source_info ADD COLUMN uniq_ruptures INTEGER;
