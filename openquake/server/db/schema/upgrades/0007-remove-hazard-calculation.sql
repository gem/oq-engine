/*
This script removes one of the core tables of the engine, the
hazard_calculation table, which has been there from day one. If you
have scripts or queries relying on that table (something that users
should not do, since the tables of the openquake database are to be
considered as private, implementation details subject to change all the
time) you will have to change them. The info of the hazard_calculation
table is now in the job_info table.
*/

ALTER TABLE hzrdi.hazard_site
DROP CONSTRAINT hzrdi_hazard_site_hazard_calculation_fk;

DROP INDEX hzrdi.hzrdi_hazard_site_location_hazard_calculation_uniq_idx;

UPDATE hzrdi.hazard_site AS y
SET hazard_calculation_id=x.id FROM uiapi.oq_job AS x
WHERE y.hazard_calculation_id=x.hazard_calculation_id;

CREATE UNIQUE INDEX hzrdi_hazard_site_location_hazard_calculation_uniq_idx
ON hzrdi.hazard_site(location, hazard_calculation_id);

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

-- updating the performance_view
DROP VIEW uiapi.performance_view;
CREATE VIEW uiapi.performance_view AS
SELECT j.value, p.* FROM (
     SELECT oq_job_id, operation, sum(duration) AS tot_duration,
     sum(duration)/maxint(count(distinct task_id)::int, 1) AS duration,
     max(pymemory)/1048576. AS pymemory, max(pgmemory)/1048576. AS pgmemory,
     count(*) AS counts
     FROM uiapi.performance
     GROUP BY oq_job_id, operation) AS p
INNER JOIN uiapi.job_param AS j
ON p.oq_job_id=j.job_id
WHERE name='description';

-- dropping the table
DROP TABLE uiapi.hazard_calculation;

-- add a forgotten geospatial index on site_model
CREATE INDEX hzrdi_site_model_location_idx
ON hzrdi.site_model USING GIST(location);

-- add a forgotten ON DELETE CASCADE on job_info
ALTER TABLE uiapi.job_info
DROP CONSTRAINT job_info_oq_job_id_fkey,
ADD CONSTRAINT job_info_oq_job_id_fkey
   FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;
