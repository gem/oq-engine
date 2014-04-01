DROP INDEX hzrdr.hzrdr_ses_rupture_tag_uniq_idx;
CREATE UNIQUE INDEX hzrdr_ses_rupture_tag_uniq_idx ON hzrdr.ses_rupture(rupture_id, tag);
ALTER TABLE hzrdr.ses_rupture DROP CONSTRAINT hzrdr_ses_rupture_ses_fk;
DROP TABLE hzrdr.ses;
