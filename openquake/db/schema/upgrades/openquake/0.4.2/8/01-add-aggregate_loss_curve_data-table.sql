/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


ALTER TABLE riskr.loss_curve ADD COLUMN aggregate BOOLEAN NOT NULL DEFAULT false;

-- Aggregate loss curve data.  Holds the probability of exceedence of certain
-- levels of losses for the whole exposure model.
CREATE TABLE riskr.aggregate_loss_curve_data (
    id SERIAL PRIMARY KEY,
    loss_curve_id INTEGER NOT NULL,

    losses float[] NOT NULL CONSTRAINT non_negative_losses
        CHECK (0 <= ALL(losses)),
    -- Probabilities of exceedence
    poes float[] NOT NULL
) TABLESPACE riskr_ts;


COMMENT ON COLUMN riskr.loss_curve.aggregate IS 'Is the curve an aggregate curve?';
COMMENT ON TABLE riskr.aggregate_loss_curve_data IS 'Holds the probabilities of exceedance for the whole exposure model.';
COMMENT ON COLUMN riskr.aggregate_loss_curve_data.loss_curve_id IS 'The foreign key to the curve record to which the loss curve data belongs';
COMMENT ON COLUMN riskr.aggregate_loss_curve_data.losses IS 'Losses';
COMMENT ON COLUMN riskr.aggregate_loss_curve_data.poes IS 'Probabilities of exceedence';


CREATE INDEX riskr_aggregate_loss_curve_data_loss_curve_id_idx on riskr.aggregate_loss_curve_data(loss_curve_id);


ALTER TABLE riskr.aggregate_loss_curve_data
ADD CONSTRAINT riskr_aggregate_loss_curve_data_loss_curve_fk
FOREIGN KEY (loss_curve_id) REFERENCES riskr.loss_curve(id) ON DELETE CASCADE;


GRANT ALL ON SEQUENCE riskr.aggregate_loss_curve_data_id_seq to GROUP openquake;

GRANT SELECT ON riskr.aggregate_loss_curve_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.aggregate_loss_curve_data TO oq_reslt_writer;
