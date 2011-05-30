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


-- Hazard map data.
CREATE TABLE uiapi.hazard_map_data (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    value float NOT NULL
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'hazard_map_data', 'location', 4326, 'POINT', 2);
ALTER TABLE uiapi.hazard_map_data ALTER COLUMN point SET NOT NULL;

ALTER TABLE uiapi.hazard_map_data
ADD CONSTRAINT uiapi_hazard_map_data_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;


-- Loss map data.
CREATE TABLE uiapi.loss_map_data (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    value float NOT NULL
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'loss_map_data', 'location', 4326, 'POINT', 2);
ALTER TABLE uiapi.loss_map_data ALTER COLUMN point SET NOT NULL;

ALTER TABLE uiapi.loss_map_data
ADD CONSTRAINT uiapi_loss_map_data_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;
