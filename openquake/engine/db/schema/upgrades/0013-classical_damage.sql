-- Damage curve
CREATE TABLE riskr.damage (
    id SERIAL PRIMARY KEY,
    risk_calculation_id INTEGER NOT NULL REFERENCES uiapi.oq_job,
    output_id INTEGER NOT NULL REFERENCES uiapi.output,
    hazard_output_id INTEGER NULL REFERENCES uiapi.output,
    statistics VARCHAR CONSTRAINT loss_curve_statistics
        CHECK(statistics IS NULL OR
              statistics IN ('mean', 'quantile')),
    -- Quantile value (only for "quantile" statistics)
    quantile float CONSTRAINT damage_quantile_value
        CHECK(
            ((statistics = 'quantile') AND (quantile IS NOT NULL))
            OR (((statistics != 'quantile') AND (quantile IS NULL))))
) TABLESPACE riskr_ts;

GRANT SELECT,INSERT ON riskr.damage TO oq_job_init;
GRANT USAGE ON riskr.damage_id_seq TO oq_job_init;

COMMENT ON TABLE riskr.damage IS 'Holds the parameters common to a set of damage curves.';
COMMENT ON COLUMN riskr.damage.output_id IS 'The foreign key to the output record that represents the corresponding damage curve.';

-- Damage curve data
CREATE TABLE riskr.damage_data (
    id SERIAL PRIMARY KEY,
    damage_id INTEGER NOT NULL REFERENCES riskr.damage,
    dmg_state_id INTEGER NOT NULL REFERENCES riskr.dmg_state,
    exposure_data_id INTEGER NOT NULL REFERENCES riski.exposure_data,
    fraction FLOAT NOT NULL
) TABLESPACE riskr_ts;


GRANT SELECT,INSERT ON riskr.damage_data TO oq_job_init;
GRANT USAGE ON riskr.damage_data_id_seq TO oq_job_init;

COMMENT ON TABLE riskr.damage_data IS 'Holds the damage fractions for a given damage curve.';
COMMENT ON COLUMN riskr.damage_data.damage_id IS 'The foreign key to the damage curve to which the damage data belongs';
COMMENT ON COLUMN riskr.damage_data.dmg_state_id IS 'The damage state id';
COMMENT ON COLUMN riskr.damage_data.exposure_data_id IS 'The asset id';
COMMENT ON COLUMN riskr.damage_data.fraction IS 'The damage fraction';

-- TODO: add indices where useful
