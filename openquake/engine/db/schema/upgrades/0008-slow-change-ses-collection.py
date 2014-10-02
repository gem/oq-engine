##########################################################################
# This script is slow only if your table hzrdr.probabilistic_rupture     #
# contains million of rows, i.e. only if you ran very large event based  #
# calculations. If this is not the case, don't worry.                    #
##########################################################################


GET_SESCOLL_AND_JOBS = """\
SELECT a.id AS ses_coll_id, b.oq_job_id
FROM hzrdr.ses_collection AS a, uiapi.output as b
WHERE output_id=b.id AND lt_model_id IS NULL;
"""

CREATE_LT_MODEL = """\
INSERT INTO hzrdr.lt_source_model
(hazard_calculation_id, ordinal, sm_lt_path, sm_name)
VALUES (%s, 0, '{}', 'fake-from-rupture')
RETURNING id;
"""

UPDATE_SES_COLL = """\
UPDATE hzrdr.ses_collection AS x
SET lt_model_id=%s WHERE id=%s;
"""

FIND_SES_COLLECTION_TRT_MODELS = '''\
SELECT hazard_calculation_id, a.id, array_agg(b.id) AS trt_model_ids
FROM hzrdr.ses_collection AS a,
hzrdr.trt_model AS b,
hzrdr.lt_source_model AS c
WHERE a.lt_model_id=b.lt_model_id
AND b.lt_model_id=c.id
GROUP BY hazard_calculation_id, a.id
ORDER BY hazard_calculation_id, a.id;
'''

CREATE_OUTPUT = '''\
INSERT INTO uiapi.output (oq_job_id, display_name, output_type)
VALUES (%s, 'SES Collection {}', 'ses')
RETURNING id
'''
CREATE_SES_COLL = '''\
INSERT INTO hzrdr.ses_collection (output_id, ordinal, trt_model_id)
VALUES (%s, %s, %s)
RETURNING id
'''

ADD_TRT_MODEL_ID = '''\
ALTER TABLE hzrdr.ses_collection
ADD COLUMN trt_model_id INTEGER
REFERENCES hzrdr.trt_model (id)
'''

UPDATE_PROB_RUPTURE = '''\
UPDATE hzrdr.probabilistic_rupture
SET ses_collection_id=%s WHERE trt_model_id=%s
'''

DROP_COLUMNS = '''\
ALTER TABLE hzrdr.ses_collection DROP COLUMN lt_model_id;
ALTER TABLE hzrdr.probabilistic_rupture DROP COLUMN trt_model_id;
'''

DELETE_OLD_SES = '''\
DELETE FROM hzrdr.ses_collection WHERE id IN %s
'''


def create_ses_collections(conn):
    assocs, old_ids = [], []
    st = conn.run(FIND_SES_COLLECTION_TRT_MODELS)
    for oq_job_id, ses_coll_id, trt_model_ids in st:
        old_ids.append(ses_coll_id)
        for ordinal, trt_model_id in enumerate(trt_model_ids, 1):
            [[output_id]] = conn.run(
                CREATE_OUTPUT.format(ordinal), oq_job_id)
            [[sc_id]] = conn.run(
                CREATE_SES_COLL, output_id, ordinal, trt_model_id)
            assocs.append((sc_id, trt_model_id))
    return assocs, old_ids


def upgrade(conn):
    # fix the records ses_collection.lt_model_id IS NULL
    for ses_coll_id, oq_job_id in conn.run(GET_SESCOLL_AND_JOBS):
        [[lt_model_id]] = conn.run(CREATE_LT_MODEL, oq_job_id)
        conn.run(UPDATE_SES_COLL, lt_model_id, ses_coll_id)

    # now all the records are NOT NULL; fix them all
    conn.run(ADD_TRT_MODEL_ID)
    assocs, old_ids = create_ses_collections(conn)
    sc_ids = set()
    for sc_id, trt_model_id in assocs:
        conn.run(UPDATE_PROB_RUPTURE, sc_id, trt_model_id)
        sc_ids.add(sc_id)
    conn.run(DELETE_OLD_SES, tuple(old_ids))
    conn.run(DROP_COLUMNS)

if __name__ == '__main__':
    from openquake.engine.db.upgrade_manager import run_script
    run_script(upgrade, rollback=True)
