CREATE TABLE hzrdr.lt_source_model (
   id SERIAL PRIMARY KEY,
   hazard_calculation_id INTEGER NOT NULL,
   ordinal INTEGER NOT NULL,
   sm_lt_path VARCHAR[] NOT NULL
) TABLESPACE hzrdr_ts;

ALTER TABLE hzrdr.lt_source_model OWNER TO oq_admin;

GRANT SELECT, INSERT ON hzrdr.lt_source_model TO oq_job_init;
GRANT USAGE ON hzrdr.lt_source_model_id_seq TO oq_job_init;

INSERT INTO hzrdr.lt_source_model (hazard_calculation_id, ordinal, sm_lt_path)
SELECT hazard_calculation_id, max(id)- min(id), sm_lt_path
FROM hzrdr.lt_realization GROUP BY hazard_calculation_id, sm_lt_path;

ALTER TABLE hzrdr.lt_realization ADD COLUMN lt_model_id INTEGER;

UPDATE hzrdr.lt_realization AS r
SET lt_model_id=m.id FROM hzrdr.lt_source_model AS m
WHERE m.hazard_calculation_id=r.hazard_calculation_id
AND m.sm_lt_path=r.sm_lt_path;

ALTER TABLE hzrdr.lt_realization ALTER COLUMN lt_model_id SET NOT NULL;

ALTER TABLE hzrdr.lt_realization DROP COLUMN sm_lt_path;
ALTER TABLE hzrdr.lt_realization DROP COLUMN hazard_calculation_id;

ALTER TABLE hzrdr.ses_collection ADD COLUMN lt_model_id INTEGER;

UPDATE hzrdr.ses_collection SET lt_model_id=l.lt_model_id
FROM hzrdr.lt_realization AS l
WHERE lt_realization_ids[1] = l.id;

ALTER TABLE hzrdr.ses_collection ALTER COLUMN lt_model_id SET NOT NULL;
ALTER TABLE hzrdr.ses_collection DROP COLUMN lt_realization_ids;

-- hzrdr.lt_source_model -> uiapi.hazard_calculation FK
ALTER TABLE hzrdr.lt_source_model
ADD CONSTRAINT hzrdr_lt_model_hazard_calculation_fk
FOREIGN KEY (hazard_calculation_id)
REFERENCES uiapi.hazard_calculation(id)
ON DELETE CASCADE;

-- hzrdr.lt_realization -> hzrdr.lt_source_model FK
ALTER TABLE hzrdr.lt_realization
ADD CONSTRAINT hzrdr_lt_realization_lt_model_fk
FOREIGN KEY (lt_model_id) REFERENCES hzrdr.lt_source_model(id)
ON DELETE CASCADE;

-- hzrdr.ses_collection -> hzrdr.lt_source_model FK
ALTER TABLE hzrdr.ses_collection
ADD CONSTRAINT hzrdr_ses_collection_lt_model_fk
FOREIGN KEY (lt_model_id) REFERENCES hzrdr.lt_source_model(id)
ON DELETE CASCADE;
