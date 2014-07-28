UPDATE uiapi.risk_calculation SET master_seed=42 WHERE master_seed IS NULL;
ALTER TABLE uiapi.risk_calculation ALTER COLUMN master_seed SET NOT NULL;

UPDATE uiapi.hazard_calculation SET random_seed=42 WHERE random_seed IS NULL;
ALTER TABLE uiapi.hazard_calculation ALTER COLUMN random_seed SET NOT NULL;
