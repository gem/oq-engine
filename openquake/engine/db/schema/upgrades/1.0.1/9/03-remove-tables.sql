DROP TABLE uiapi.job_phase_stats;
DROP TABLE htemp.source_progress;
DROP TABLE hzrdi.parsed_source;

ALTER TABLE uiapi.hazard_calculation DROP COLUMN no_progress_timeout;
ALTER TABLE uiapi.risk_calculation DROP COLUMN no_progress_timeout;

ALTER TABLE uiapi.hazard_calculation DROP COLUMN complete_logic_tree_ses;
ALTER TABLE uiapi.hazard_calculation DROP COLUMN complete_logic_tree_gmf;

DELETE FROM hzrdr.ses_collection WHERE lt_realization_id IS NULL;
ALTER TABLE hzrdr.ses_collection ALTER COLUMN lt_realization_id SET NOT NULL;

-- I don't want to remove data from the user machines, so the following
-- two lines are commented off, but you can uncomment them if you want
-- a full cleanup of the db
-- DELETE FROM uiapi.output WHERE output_type='complete_lt_ses';
-- DELETE FROM uiapi.output WHERE output_type='complete_lt_gmf';
