-- OQ_USER
ALTER TABLE uiapi.oq_job ADD user_name VARCHAR;
UPDATE uiapi.oq_job SET user_name = (SELECT user_name FROM admin.oq_user WHERE id=uiapi.oq_job.owner_id);
ALTER TABLE uiapi.oq_job ALTER user_name SET NOT NULL;
ALTER TABLE uiapi.risk_calculation DROP owner_id;
ALTER TABLE uiapi.hazard_calculation DROP owner_id;
ALTER TABLE uiapi.input DROP owner_id;
ALTER TABLE uiapi.oq_job DROP owner_id;
ALTER TABLE uiapi.output DROP owner_id;
DROP TABLE admin.oq_user;

-- OQ_ORGANIZATION
DROP TABLE admin.organization;



