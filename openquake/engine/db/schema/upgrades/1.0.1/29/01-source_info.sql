CREATE TABLE hzrdr.source_info (
  id SERIAL,
  trt_model_id INTEGER NOT NULL,
  source_id TEXT NOT NULL,
  source_class TEXT NOT NULL,
  num_sites INTEGER NOT NULL,
  num_ruptures INTEGER NOT NULL,
  occ_ruptures INTEGER NOT NULL,
  calc_time FLOAT NOT NULL);

ALTER TABLE hzrdr.source_info OWNER TO oq_admin;

GRANT SELECT, INSERT ON hzrdr.source_info TO oq_job_init;
GRANT USAGE ON hzrdr.source_info_id_seq TO oq_job_init;

ALTER TABLE hzrdr.source_info ADD CONSTRAINT hzrdr_source_info_trt_model_fk
FOREIGN KEY (trt_model_id) REFERENCES hzrdr.trt_model(id)
ON DELETE CASCADE;

