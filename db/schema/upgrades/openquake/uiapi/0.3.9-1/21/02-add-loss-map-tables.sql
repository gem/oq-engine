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

CREATE TABLE uiapi.loss_map (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    deterministic BOOLEAN NOT NULL,
    loss_map_ref VARCHAR,
    end_branch_label VARCHAR,
    category VARCHAR,
    unit VARCHAR, -- e.g. USD, EUR
    -- poe and investigation_time are significant only for non deterministic calculations
    -- investigation_time is stored in the oq_params table
    poe float CONSTRAINT valid_poe
        CHECK ((NOT deterministic AND (poe >= 0.0) AND (poe <= 1.0))
               OR (deterministic AND poe IS NULL))
) TABLESPACE uiapi_ts;

CREATE TABLE uiapi.loss_map_data (
    id SERIAL PRIMARY KEY,
    loss_map_id INTEGER NOT NULL, -- FK to loss_map.id
    asset_ref VARCHAR NOT NULL,
    value float NOT NULL,
    std_dev float NOT NULL DEFAULT 0.0 -- for non deterministic calculations std_dev is 0
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
