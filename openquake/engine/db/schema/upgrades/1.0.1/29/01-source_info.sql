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


CREATE VIEW hzrdr.source_progress AS
SELECT a.hazard_calculation_id, sources_done, sources_todo FROM
   (SELECT y.hazard_calculation_id, count(x.id) AS sources_done
   FROM hzrdr.source_info AS x, hzrdr.lt_source_model AS y, hzrdr.trt_model AS z
   WHERE x.trt_model_id = z.id AND z.lt_model_id=y.id
   GROUP BY y.hazard_calculation_id) AS a,
   (SELECT y.hazard_calculation_id, sum(num_sources) AS sources_todo
   FROM hzrdr.lt_source_model AS y, hzrdr.trt_model AS z
   WHERE z.lt_model_id=y.id
   GROUP by y.hazard_calculation_id) AS b
WHERE a.hazard_calculation_id=b.hazard_calculation_id;

ALTER VIEW hzrdr.source_progress OWNER TO oq_admin;
