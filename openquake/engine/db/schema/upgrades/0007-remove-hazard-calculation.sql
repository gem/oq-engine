ALTER TABLE hzrdi.hazard_site
DROP CONSTRAINT hzrdi_hazard_site_hazard_calculation_fk;

UPDATE hzrdi.hazard_site AS y
SET hazard_calculation_id=x.id FROM uiapi.oq_job AS x
WHERE y.hazard_calculation_id=x.hazard_calculation_id;

ALTER TABLE hzrdi.hazard_site 
ADD CONSTRAINT hzrdi_hazard_site_oq_job_fk
FOREIGN KEY (hazard_calculation_id)
REFERENCES uiapi.oq_job(id)
ON DELETE CASCADE;

ALTER TABLE hzrdr.lt_source_model
DROP CONSTRAINT hzrdr_lt_model_hazard_calculation_fk;

UPDATE hzrdr.lt_source_model AS y
SET hazard_calculation_id=x.id FROM uiapi.oq_job AS x
WHERE y.hazard_calculation_id=x.hazard_calculation_id;

ALTER TABLE hzrdr.lt_source_model 
ADD CONSTRAINT hzrdr_lt_source_model_oq_job_fk
FOREIGN KEY (hazard_calculation_id)
REFERENCES uiapi.oq_job(id)
ON DELETE CASCADE;

UPDATE uiapi.risk_calculation AS y
SET hazard_calculation_id=x.id FROM uiapi.oq_job AS x
WHERE y.hazard_calculation_id=x.hazard_calculation_id;

ALTER TABLE uiapi.oq_job
DROP CONSTRAINT uiapi_oq_job_hazard_calculation;

DROP VIEW uiapi.performance_view;

CREATE VIEW uiapi.performance_view AS
SELECT o.id AS calculation_id, value, 'hazard' AS job_type, p.* FROM (
     SELECT oq_job_id, operation,
     sum(duration) AS tot_duration,
     sum(duration)/maxint(count(distinct task_id)::int, 1) AS duration,
     max(pymemory)/1048576. AS pymemory, max(pgmemory)/1048576. AS pgmemory,
     count(*) AS counts
     FROM uiapi.performance
     GROUP BY oq_job_id, operation) AS p
INNER JOIN uiapi.oq_job AS o
ON p.oq_job_id=o.id
INNER JOIN uiapi.job_param AS h
ON h.job_id=o.id WHERE name='description'
UNION ALL
SELECT r.id AS calculation_id, description, 'risk' AS job_type, p.* FROM (
     SELECT oq_job_id, operation,
     sum(duration) AS tot_duration,
     sum(duration)/maxint(count(distinct task_id)::int, 1) AS duration,
     max(pymemory)/1048576. AS pymemory, max(pgmemory)/1048576. AS pgmemory,
     count(*) AS counts
     FROM uiapi.performance
     GROUP BY oq_job_id, operation) AS p
INNER JOIN uiapi.oq_job AS o
ON p.oq_job_id=o.id
INNER JOIN uiapi.risk_calculation AS r
ON r.id=o.risk_calculation_id;

DROP TABLE uiapi.hazard_calculation;

-- TODO: drop the site_model table, now useless

GRANT SELECT,INSERT,UPDATE ON uiapi.job_param TO oq_job_init;
