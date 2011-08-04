/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- Loss asset data.
CREATE TABLE uiapi.loss_asset_data (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    asset_id VARCHAR,
    UNIQUE (output_id, asset_id)
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'loss_asset_data', 'pos', 4326, 'POINT', 2);
ALTER TABLE uiapi.loss_asset_data ALTER COLUMN pos SET NOT NULL;


-- Loss curve data.
CREATE TABLE uiapi.loss_curve_data (
    id SERIAL PRIMARY KEY,
    loss_asset_id INTEGER NOT NULL,
    end_branch_label VARCHAR,
    abscissae float[] NOT NULL,
    poes float[] NOT NULL
) TABLESPACE uiapi_ts;

CREATE INDEX uiapi_loss_asset_data_output_id_idx on uiapi.loss_asset_data(output_id);
CREATE INDEX uiapi_loss_curve_data_loss_asset_id_idx on uiapi.loss_curve_data(loss_asset_id);

ALTER TABLE uiapi.loss_asset_data
ADD CONSTRAINT uiapi_loss_asset_data_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE uiapi.loss_curve_data
ADD CONSTRAINT uiapi_loss_curve_data_loss_asset_fk
FOREIGN KEY (loss_asset_id) REFERENCES uiapi.loss_asset_data(id) ON DELETE CASCADE;
