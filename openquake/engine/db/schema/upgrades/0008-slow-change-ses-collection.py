##########################################################################
# This script is slow only if your table hzrdr.probabilistic_rupture     #
# contains million of rows, i.e. only if you ran very large event based  #
# calculations. If this is not the case, don't worry.                    #
##########################################################################


def fix_null_lt_models(conn):
    # find the records where ses_collection.lt_model_id is NULL
    for ses_coll_id, oq_job_id in conn.run("""\
SELECT a.id, b.oq_job_id
FROM hzrdr.ses_collection AS a, uiapi.output as b
WHERE output_id=b.id AND lt_model_id IS NULL"""):

        # insert a fake source model for each record
        [[lt_model_id]] = conn.run("""\
INSERT INTO hzrdr.lt_source_model
(hazard_calculation_id, ordinal, sm_lt_path, sm_name)
VALUES (%s, 0, '{}', 'fake-from-rupture')
RETURNING id""", oq_job_id)

        # insert a fake trt model
        conn.run("""\
INSERT INTO hzrdr.trt_model
(lt_model_id, tectonic_region_type, num_sources, num_ruptures,
 min_mag, max_mag, gsims)
VALUES (%s, 'NA', 0, 1, 0, 0, '{}')
RETURNING id""", lt_model_id)

        # update ses_collection.lt_model_id
        conn.run("""\
UPDATE hzrdr.ses_collection AS x
SET lt_model_id=%s WHERE id=%s""", lt_model_id, ses_coll_id)


def create_ses_collections(conn):
    # create new ses_collections for each trt_model
    assocs, old_ids = [], []
    # find the associations ses_coll_id -> trt_model_ids
    cursor = conn.run("""\
SELECT hazard_calculation_id, a.id, array_agg(b.id) AS trt_model_ids
FROM hzrdr.ses_collection AS a,
hzrdr.trt_model AS b,
hzrdr.lt_source_model AS c
WHERE a.lt_model_id=b.lt_model_id
AND b.lt_model_id=c.id
GROUP BY hazard_calculation_id, a.id
ORDER BY hazard_calculation_id, a.id""")
    for oq_job_id, ses_coll_id, trt_model_ids in cursor:
        old_ids.append(ses_coll_id)
        for ordinal, trt_model_id in enumerate(trt_model_ids, 1):

            # create a new output for each trt_model
            [[output_id]] = conn.run('''\
INSERT INTO uiapi.output (oq_job_id, display_name, output_type)
VALUES (%s, 'SES Collection {}', 'ses')
RETURNING id'''.format(ordinal), oq_job_id)

            # create a new ses_collection for each output
            [[sc_id]] = conn.run('''\
INSERT INTO hzrdr.ses_collection (output_id, ordinal, trt_model_id)
VALUES (%s, %s, %s)
RETURNING id''', output_id, ordinal, trt_model_id)
            assocs.append((sc_id, trt_model_id))

    return assocs, old_ids


def upgrade(conn):
    # first of all, fix the NULLs in ses_collection.lt_model_id
    fix_null_lt_models(conn)

    # add a column ses_collection.trt_model_id
    conn.run('''\
ALTER TABLE hzrdr.ses_collection
ADD COLUMN trt_model_id INTEGER
REFERENCES hzrdr.trt_model (id)''')
    # create new ses_collections for each trt_model
    assocs, old_ids = create_ses_collections(conn)
    ses_coll_ids = set()  # new ses_collections
    for ses_coll_id, trt_model_id in assocs:
        # set probabilistic_rupture.ses_collection_id to the new ses_collection
        conn.run("""\
UPDATE hzrdr.probabilistic_rupture
SET ses_collection_id=%s WHERE trt_model_id=%s""", ses_coll_id, trt_model_id)
        ses_coll_ids.add(ses_coll_id)
    if old_ids:
        # remove the old outputs
        conn.run("""\
DELETE FROM uiapi.output WHERE id IN (
SELECT output_id FROM hzrdr.ses_collection WHERE id IN %s)""", tuple(old_ids))
        # remove the old ses_collections
        conn.run("DELETE FROM hzrdr.ses_collection WHERE id IN %s",
                 tuple(old_ids))

    # drop the now redundant columns lt_model_id and trt_model_id
    conn.run("""\
ALTER TABLE hzrdr.ses_collection DROP COLUMN lt_model_id;
ALTER TABLE hzrdr.probabilistic_rupture DROP COLUMN trt_model_id;""")

if __name__ == '__main__':
    from openquake.engine.db.upgrade_manager import check_script
    check_script(upgrade, rollback=True)
