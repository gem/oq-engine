/*
    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License version 3
    only, as published by the Free Software Foundation.

    OpenQuake is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License version 3 for more details
    (a copy is included in the LICENSE file that accompanied this code).

    You should have received a copy of the GNU Lesser General Public License
    version 3 along with OpenQuake.  If not, see
    <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.
*/

-- Loss asset data.
CREATE TABLE uiapi.loss_asset_data (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    asset_id VARCHAR
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
