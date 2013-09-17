ALTER TABLE uiapi.model_content DROP COLUMN raw_content;
ALTER TABLE uiapi.model_content ADD COLUMN raw_content BYTEA NOT NULL DEFAULT '';
