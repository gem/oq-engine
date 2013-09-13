ALTER TABLE hzrdr.ses_rupture ADD COLUMN tag VARCHAR;

CREATE INDEX hzrdr_ses_rupture_tag_idx ON hzrdr.ses_rupture (tag);
