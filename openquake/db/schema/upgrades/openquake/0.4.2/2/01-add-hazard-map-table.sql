/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- Hazard map header
CREATE TABLE uiapi.hazard_map (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    poe float NOT NULL,
    -- Statistic type, one of:
    --      mean
    --      quantile
    statistic_type VARCHAR CONSTRAINT statistic_type_value
        CHECK(statistic_type IN ('mean', 'quantile')),
    -- Quantile value (only for "quantile" statistics)
    quantile float CONSTRAINT quantile_value
        CHECK(
            ((statistic_type = 'quantile') AND (quantile IS NOT NULL))
            OR (((statistic_type <> 'quantile') AND (quantile IS NULL))))
) TABLESPACE uiapi_ts;

-- Hazard map data
ALTER TABLE uiapi.hazard_map_data
    DROP CONSTRAINT uiapi_hazard_map_data_output_fk;
ALTER TABLE uiapi.hazard_map_data RENAME COLUMN output_id TO hazard_map_id;

-- indices
CREATE INDEX uiapi_hazard_map_output_id_idx on uiapi.hazard_map(output_id);

-- foreign keys
ALTER TABLE uiapi.hazard_map
ADD CONSTRAINT uiapi_hazard_map_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

-- comments
COMMENT ON TABLE uiapi.hazard_map IS 'Holds location/IML data for hazard maps';
COMMENT ON COLUMN uiapi.hazard_map.output_id IS 'The foreign key to the hazard map record that represents the corresponding hazard map.';
COMMENT ON COLUMN uiapi.hazard_map.poe IS 'Probability of exceedence';
COMMENT ON COLUMN uiapi.hazard_map.statistic_type IS 'Statistic type, one of:
    - Median   (median)
    - Quantile (quantile)';
COMMENT ON COLUMN uiapi.hazard_map.quantile IS 'The quantile for quantile statistical data.';

COMMENT ON COLUMN uiapi.hazard_map_data.hazard_map_id IS 'The foreign key to the hazard map record that represents the corresponding hazard map.';
COMMENT ON COLUMN uiapi.hazard_map_data.location IS 'Position in the hazard map';
COMMENT ON COLUMN uiapi.hazard_map_data.value IS 'IML value for this location';

-- permissions
GRANT ALL ON SEQUENCE uiapi.hazard_map_id_seq to GROUP openquake;

-- uiapi.hazard_map
GRANT SELECT ON uiapi.hazard_map TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.hazard_map TO oq_uiapi_writer;
