-- first some missing GRANTs on the table imt
GRANT SELECT,INSERT ON hzrdi.imt TO oq_job_init;
GRANT USAGE ON hzrdi.imt_id_seq TO oq_job_init;


CREATE TABLE riski.imt_taxonomy (
   id SERIAL PRIMARY KEY,
   job_id INTEGER NOT NULL REFERENCES uiapi.oq_job (id) ON DELETE CASCADE,
   imt_id INTEGER NOT NULL REFERENCES hzrdi.imt (id) ON DELETE CASCADE,
   taxonomy TEXT NOT NULL,
    UNIQUE (job_id, taxonomy, imt_id)
) TABLESPACE riski_ts;

GRANT SELECT,INSERT ON riski.imt_taxonomy TO oq_job_init;
GRANT USAGE ON riski.imt_taxonomy_id_seq TO oq_job_init;

COMMENT ON TABLE riski.imt_taxonomy IS 'Associations between IMTs and taxonomies for each loss type';
COMMENT ON COLUMN riski.imt_taxonomy.job_id IS 'The job performing the association';
COMMENT ON COLUMN riski.imt_taxonomy.imt_id IS 'The IMT ID)';
