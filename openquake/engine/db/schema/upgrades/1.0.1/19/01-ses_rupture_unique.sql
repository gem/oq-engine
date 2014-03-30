/*
A bug was introduced in march 2014 with the refactoring to remove
the ruptures as pickled objects. This is why duplicated rupture
tags may appear in the ses_rupture table. If this upgrade script
fails, just remove the duplicates with the following query:

DELETE FROM hzrdr.ses_rupture AS x USING (
   SELECT ses_id, tag FROM hzrdr.ses_rupture
   GROUP BY ses_id, tag HAVING count(*) > 1) AS y
WHERE x.ses_id=y.ses_id AND x.tag=y.tag;

This is the only viable approach, since if you have duplicated tags
in the database the risk results are not reliable, depending on the
random order the ruptures are extracted from the database.

Since we not want to delete data from the user database without
warning, the query is commented and must be executed manually.
*/

CREATE UNIQUE INDEX hzrdr_ses_rupture_tag_uniq_idx
ON hzrdr.ses_rupture(ses_id, tag);
