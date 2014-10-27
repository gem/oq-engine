UPDATE uiapi.oq_job AS x
SET hazard_calculation_id=y.hazard_calculation_id
FROM uiapi.risk_calculation AS y
WHERE x.risk_calculation_id=y.id
AND x.hazard_calculation_id IS NULL;

ALTER TABLE uiapi.oq_job
DROP COLUMN risk_calculation_id;

ALTER TABLE uiapi.oq_job
ADD CONSTRAINT oq_job_oq_job_id_fkey
FOREIGN KEY (hazard_calculation_id)
REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

ALTER TABLE riskr.dmg_state
DROP CONSTRAINT dmg_state_risk_calculation_id_fkey,
ADD CONSTRAINT dmg_state_oq_job_id_fkey
FOREIGN KEY (risk_calculation_id)
REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;

DROP TABLE uiapi.risk_calculation;
