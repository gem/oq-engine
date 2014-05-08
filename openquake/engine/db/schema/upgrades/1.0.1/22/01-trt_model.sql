-- trt_model table --
ALTER TABLE hzrdr.lt_model_info RENAME TO trt_model;
ALTER TABLE hzrdr.trt_model ADD COLUMN gsims TEXT[];

GRANT UPDATE ON hzrdr.trt_model TO oq_job_init;


-- assoc_lt_rlz_trt_model table --
CREATE TABLE hzrdr.assoc_lt_rlz_trt_model(
id SERIAL,
rlz_id INTEGER NOT NULL,
trt_model_id INTEGER NOT NULL,
gsim TEXT NOT NULL);


ALTER TABLE hzrdr.assoc_lt_rlz_trt_model OWNER TO oq_admin;

GRANT SELECT, INSERT ON hzrdr.assoc_lt_rlz_trt_model TO oq_job_init;
GRANT USAGE ON hzrdr.assoc_lt_rlz_trt_model_id_seq TO oq_job_init;

-- index on  (trt_model_id, gsim)
CREATE INDEX hzrdr_assoc_lt_rlz_trt_model_gsim_idx
ON hzrdr.assoc_lt_rlz_trt_model (trt_model_id, gsim);

-- hzrdr.assoc_lt_rlz_trt_model -> hzrdr.lt_realization FK
ALTER TABLE hzrdr.assoc_lt_rlz_trt_model
ADD CONSTRAINT hzrdr_assoc_lt_rlz_trt_model_fk1
FOREIGN KEY (rlz_id)
REFERENCES hzrdr.lt_realization(id)
ON DELETE CASCADE;


-- hzrdr.assoc_lt_rlz_trt_model -> hzrdr.trt_model FK
ALTER TABLE hzrdr.assoc_lt_rlz_trt_model
ADD CONSTRAINT hzrdr_trt_model_lt_source_model_fk2
FOREIGN KEY (trt_model_id)
REFERENCES hzrdr.trt_model(id)
ON DELETE CASCADE;
