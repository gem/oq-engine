"""
Fix the SES collections with NULL source model (the ones associated to
scenario calculations) by creating fake source models for them.
Then add a NOT NULL constraint on lt_model_id.
"""


GET_SESCOLL_AND_JOBS = """\
SELECT a.id AS ses_coll_id, b.oq_job_id
FROM hzrdr.ses_collection AS a, uiapi.output as b
WHERE output_id=b.id AND lt_model_id IS NULL;
"""

CREATE_LT_MODEL = """\
INSERT INTO hzrdr.lt_source_model
(hazard_calculation_id, ordinal, sm_lt_path, sm_name)
VALUES (%s, 0, %s, 'fake-from-rupture')
RETURNING id;
"""

UPDATE_SES_COLL = """\
UPDATE hzrdr.ses_collection
SET lt_model_id=%s WHERE id=%s;
"""

FIX_SES_COLL = """\
TRUNCATE TABLE hzrdr.ses_collection CASCADE;  -- to fix

ALTER TABLE hzrdr.ses_collection ADD COLUMN trt_model_id INTEGER NOT NULL
REFERENCES hzrdr.trt_model (id);

ALTER TABLE hzrdr.ses_collection DROP COLUMN lt_model_id;

ALTER TABLE hzrdr.probabilistic_rupture DROP COLUMN trt_model_id;
"""


def upgrade(conn):
    curs = conn.cursor()
    curs.execute(GET_SESCOLL_AND_JOBS)
    for ses_coll_id, oq_job_id in curs.fetchall():
        curs.execute(CREATE_LT_MODEL, (oq_job_id, []))
        [[lt_model_id]] = curs.fetchall()
        curs.execute(UPDATE_SES_COLL, (lt_model_id, ses_coll_id))
    curs.execute(FIX_SES_COLL)
