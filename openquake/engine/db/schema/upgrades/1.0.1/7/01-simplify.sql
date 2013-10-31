-- OQ_USER
ALTER TABLE uiapi.oq_job ADD user_name VARCHAR;
UPDATE uiapi.oq_job SET user_name = (SELECT user_name FROM admin.oq_user WHERE id=uiapi.oq_job.owner_id);
ALTER TABLE uiapi.oq_job ALTER user_name SET NOT NULL;
ALTER TABLE uiapi.risk_calculation DROP owner_id;
ALTER TABLE uiapi.hazard_calculation DROP owner_id;
ALTER TABLE uiapi.input DROP owner_id;
ALTER TABLE uiapi.oq_job DROP owner_id;
ALTER TABLE uiapi.output DROP owner_id;
DROP TRIGGER admin_oq_user_refresh_last_update_trig;
DROP TABLE admin.oq_user;

-- OQ_ORGANIZATION
DROP TRIGGER admin_organization_refresh_last_update_trig;
DROP TABLE admin.organization;


-- OQ_INPUT
ALTER TABLE hzrdi.site_model ADD job_id INTEGER NULL;
UPDATE hzrdi.site_model SET job_id=(
       SELECT job.id FROM uiapi.oq_job AS job
       JOIN uiapi.hazard_calculation AS hc ON hc.id = job.hazard_calculation_id
       JOIN uiapi.input2hcalc AS i2h ON i2h.hazard_calculation_id = hc.id
       WHERE i2h.input_id = input_id) WHERE job_id IS NULL;
ALTER TABLE hzrdi.site_model DROP input_id;

ALTER TABLE hzrdi.site_model ADD CONSTRAINT hzrdi_site_model_job_fk
FOREIGN KEY (job_id) REFERENCES uiapi.job(id) ON DELETE RESTRICT;

ALTER TABLE hzrdi.parsed_source ADD job_id INTEGER NULL;
UPDATE hzrdi.parsed_source SET job_id=(
       SELECT job.id FROM uiapi.oq_job AS job
       JOIN uiapi.hazard_calculation AS hc ON hc.id = job.hazard_calculation_id
       JOIN uiapi.input2hcalc AS i2h ON i2h.hazard_calculation_id = hc.id
       WHERE i2h.input_id = input_id) WHERE job_id IS NULL;
ALTER TABLE hzrdi.parsed_source DROP input_id;

ALTER TABLE hzrdi.parsed_source ADD CONSTRAINT hzrdi_parsed_source_job_fk
FOREIGN KEY (job_id) REFERENCES uiapi.job(id) ON DELETE RESTRICT;


ALTER TABLE hzrdi.parsed_rupture_model ADD job_id INTEGER NULL;
UPDATE hzrdi.parsed_rupture_model SET job_id=(
       SELECT job.id FROM uiapi.oq_job AS job
       JOIN uiapi.hazard_calculation AS hc ON hc.id = job.hazard_calculation_id
       JOIN uiapi.input2hcalc AS i2h ON i2h.hazard_calculation_id = hc.id
       WHERE i2h.input_id = input_id) WHERE job_id IS NULL;
ALTER TABLE hzrdi.parsed_rupture_model DROP input_id;

ALTER TABLE hzrdi.parsed_rupture_model ADD CONSTRAINT hzrdi_parsed_rupture_model_job_fk
FOREIGN KEY (job_id) REFERENCES uiapi.job(id) ON DELETE RESTRICT;


ALTER TABLE uiapi.risk_calculation ADD preloaded_exposure_model_id INTEGER;
UPDATE uiapi.risk_calculation SET preloaded_exposure_model_id=(
       SELECT em.id FROM riski.exposure_model AS em
       WHERE em.input_id = exposure_input_id)
WHERE exposure_input_id IS NOT NULL;
ALTER TABLE uiapi.risk_calculation DROP exposure_input_id;

ALTER TABLE uiapi.risk_calculation ADD CONSTRAINT uiapi_risk_calculation_exposure_model_fk
FOREIGN KEY (exposure_model_id) REFERENCES riski.exposure_model(id) ON DELETE RESTRICT;


ALTER TABLE riski.exposure_model ADD job_id INTEGER NULL;
UPDATE riski.exposure_model SET job_id=(
       SELECT job.id FROM uiapi.oq_job AS job
       JOIN uiapi.risk_calculation AS rc ON rc.id = job.risk_calculation_id
       JOIN uiapi.input2rcalc AS i2r ON i2r.risk_calculation_id = rc.id
       WHERE i2r.input_id = input_id) WHERE job_id IS NULL;
ALTER TABLE riski.exposure_model DROP input_id;

ALTER TABLE riski.exposure_model ADD CONSTRAINT riski_exposure_model_job_fk
FOREIGN KEY (job_id) REFERENCES uiapi.oq_job(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.hazard_calculation ADD inputs BYTEA;
ALTER TABLE uiapi.risk_calculation ADD inputs BYTEA;

DROP TABLE uiapi.model_content;
DROP TABLE uiapi.src2ltsrc;
DROP TABLE uiapi.input2job;
DROP TABLE uiapi.input2hcalc;
DROP TABLE uiapi.input2rcalc;

DROP TABLE uiapi.input;

