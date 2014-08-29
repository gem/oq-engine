DELETE FROM hzrdr.gmf_data WHERE rupture_ids IS NULL;
ALTER TABLE hzrdr.gmf_data ALTER COLUMN rupture_ids SET NOT NULL;
