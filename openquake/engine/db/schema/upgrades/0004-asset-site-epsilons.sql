CREATE TABLE riskr.asset_site (
id SERIAL PRIMARY KEY,
job_id INTEGER NOT NULL REFERENCES uiapi.oq_job (id) ON DELETE CASCADE,
asset_id INTEGER NOT NULL REFERENCES riski.exposure_data (id) ON DELETE CASCADE,
site_id INTEGER NOT NULL REFERENCES hzrdi.hazard_site (id) ON DELETE CASCADE,
UNIQUE (job_id, asset_id, site_id)
) TABLESPACE riskr_ts;

GRANT SELECT,INSERT ON riskr.asset_site TO oq_job_init;
GRANT USAGE ON riskr.asset_site_id_seq TO oq_job_init;

COMMENT ON TABLE riskr.asset_site IS 'Association between assets and hazard sites';
COMMENT ON COLUMN riskr.asset_site.job_id IS 'The job performing the association';
COMMENT ON COLUMN riskr.asset_site.asset_id IS 'The asset ID (exposure_data_id)';
COMMENT ON COLUMN riskr.asset_site.site_id IS 'The hazard site ID';


CREATE TABLE riskr.epsilon (
id SERIAL PRIMARY KEY,
asset_site_id INTEGER NOT NULL REFERENCES riskr.asset_site (id)
                               ON DELETE CASCADE,
ses_collection_id INTEGER NOT NULL REFERENCES hzrdr.ses_collection (id)
                               ON DELETE CASCADE,
epsilons FLOAT[] NOT NULL,
UNIQUE (asset_site_id, ses_collection_id)
) TABLESPACE riskr_ts;

GRANT SELECT,INSERT ON riskr.epsilon TO oq_job_init;
GRANT USAGE ON riskr.epsilon_id_seq TO oq_job_init;

COMMENT ON TABLE riskr.epsilon IS 'The epsilons for each asset and SES collection used in an event_based or scenario risk calculation';

COMMENT ON COLUMN riskr.epsilon.asset_site_id IS 'The asset and site associated to the given epsilons';

COMMENT ON COLUMN riskr.epsilon.ses_collection_id IS 'The SES collection corresponding to the given epsilons';
COMMENT ON COLUMN riskr.epsilon.epsilons IS 'The array of epsilons';
