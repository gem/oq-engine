/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

CREATE TABLE uiapi.loss_map (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    deterministic BOOLEAN NOT NULL,
    loss_map_ref VARCHAR,
    end_branch_label VARCHAR,
    category VARCHAR,
    unit VARCHAR, -- e.g. USD, EUR
    -- poe is significant only for non-deterministic calculations
    poe float CONSTRAINT valid_poe
        CHECK ((NOT deterministic AND (poe >= 0.0) AND (poe <= 1.0))
               OR (deterministic AND poe IS NULL))
) TABLESPACE uiapi_ts;

CREATE TABLE uiapi.loss_map_data (
    id SERIAL PRIMARY KEY,
    loss_map_id INTEGER NOT NULL, -- FK to loss_map.id
    asset_ref VARCHAR NOT NULL,
    value float NOT NULL,
    -- for non-deterministic calculations std_dev is 0
    std_dev float NOT NULL DEFAULT 0.0
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'loss_map_data', 'location', 4326, 'POINT', 2);
ALTER TABLE uiapi.loss_map_data ALTER COLUMN location SET NOT NULL;

ALTER TABLE uiapi.loss_map
ADD CONSTRAINT uiapi_loss_map_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE uiapi.loss_map_data
ADD CONSTRAINT uiapi_loss_map_data_loss_map_fk
FOREIGN KEY (loss_map_id) REFERENCES uiapi.loss_map(id) ON DELETE CASCADE;

CREATE INDEX uiapi_loss_map_output_id_idx on uiapi.loss_map(output_id);
CREATE INDEX uiapi_loss_map_data_loss_map_id_idx on uiapi.loss_map_data(loss_map_id);
