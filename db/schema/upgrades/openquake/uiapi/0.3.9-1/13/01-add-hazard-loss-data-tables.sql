/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


-- Hazard map data.
CREATE TABLE uiapi.hazard_map_data (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    value float NOT NULL
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'hazard_map_data', 'location', 4326, 'POINT', 2);
ALTER TABLE uiapi.hazard_map_data ALTER COLUMN location SET NOT NULL;

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
ALTER TABLE uiapi.loss_map_data ALTER COLUMN location SET NOT NULL;

ALTER TABLE uiapi.loss_map_data
ADD CONSTRAINT uiapi_loss_map_data_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;
