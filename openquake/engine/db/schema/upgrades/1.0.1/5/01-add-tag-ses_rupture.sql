ALTER TABLE hzrdr.ses_rupture ADD COLUMN tag VARCHAR;
UPDATE hzrdr.ses_rupture SET tag = id::text;
CREATE INDEX hzrdr_ses_rupture_tag_idx ON hzrdr.ses_rupture (tag);
