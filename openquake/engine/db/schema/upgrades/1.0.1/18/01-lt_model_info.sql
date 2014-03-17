-- logic tree source model infos
CREATE TABLE hzrdr.lt_model_info (
   id SERIAL PRIMARY KEY,
   lt_model_id INTEGER NOT NULL,
   tectonic_region_type TEXT NOT NULL,
   num_sources INTEGER NOT NULL,
   min_mag FLOAT NOT NULL,
   max_mag FLOAT NOT NULL
) TABLESPACE hzrdr_ts;

ALTER TABLE hzrdr.lt_model_info OWNER TO oq_admin;

GRANT SELECT, INSERT ON hzrdr.lt_model_info TO oq_job_init;
GRANT USAGE ON hzrdr.lt_model_info_id_seq TO oq_job_init;

-- hzrdr.lt_model_info -> hzrdr.lt_source_model FK
ALTER TABLE hzrdr.lt_model_info
ADD CONSTRAINT hzrdr_lt_model_info_lt_source_model_fk
FOREIGN KEY (lt_model_id)
REFERENCES hzrdr.lt_source_model(id)
ON DELETE CASCADE;
