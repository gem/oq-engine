-- remove duplicates, if any
DELETE FROM hzrdr.ses_rupture AS x USING (
   SELECT ses_id, tag FROM hzrdr.ses_rupture
   GROUP BY ses_id, tag HAVING count(*) > 1) AS y
WHERE x.ses_id=y.ses_id AND x.tag=y.tag;

CREATE UNIQUE INDEX hzrdr_ses_rupture_tag_uniq_idx
ON hzrdr.ses_rupture(ses_id, tag);
