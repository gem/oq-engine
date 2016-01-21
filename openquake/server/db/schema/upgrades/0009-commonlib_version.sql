-- nrmllib is dead; the version number has not been updated from the time of
-- 1.0, so it is meaningless and can be set to NULL to avoid confusion
UPDATE uiapi.oq_job SET nrml_version=NULL;
ALTER TABLE uiapi.oq_job RENAME COLUMN nrml_version TO commonlib_version;
