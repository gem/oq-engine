-- dropped a brain-damaged constraint
ALTER TABLE uiapi.output DROP CONSTRAINT output_type_value;

-- Event Loss table per asset
CREATE TABLE riskr.event_loss_asset (
    id SERIAL PRIMARY KEY,
    event_loss_id INTEGER NOT NULL REFERENCES riskr.event_loss (id),
    rupture_id INTEGER NOT NULL REFERENCES hzrdr.ses_rupture (id),
    asset_id INTEGER NOT NULL REFERENCES riski.exposure_data (id),
    loss FLOAT NOT NULL
) TABLESPACE riskr_ts;
   
GRANT SELECT,INSERT ON riskr.event_loss_asset TO oq_job_init;
GRANT USAGE ON riskr.event_loss_asset_id_seq TO oq_job_init;
   
COMMENT ON TABLE riskr.event_loss_asset IS 'Loss per loss_type per event per asset';
COMMENT ON COLUMN riskr.event_loss_asset.event_loss_id IS 'event_loss (id)';
COMMENT ON COLUMN riskr.event_loss_asset.rupture_id IS 'ses_rupture (id)';
COMMENT ON COLUMN riskr.event_loss_asset.asset_id IS 'exposure_data (id)';
COMMENT ON COLUMN riskr.event_loss_asset.loss IS 'Loss value';
   
   
