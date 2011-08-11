/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


-- Add additinal output type
ALTER TABLE uiapi.output DROP CONSTRAINT output_type_value;
ALTER TABLE uiapi.output ADD CONSTRAINT output_type_value
        CHECK(output_type IN ('unknown', 'hazard_curve', 'hazard_map',
            'gmf', 'loss_curve', 'loss_map'));

-- GMF data.
CREATE TABLE uiapi.gmf_data (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    -- Ground motion value
    ground_motion float NOT NULL
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'gmf_data', 'location', 4326, 'POINT', 2);
ALTER TABLE uiapi.gmf_data ALTER COLUMN location SET NOT NULL;

ALTER TABLE uiapi.gmf_data
ADD CONSTRAINT uiapi_gmf_data_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

CREATE INDEX uiapi_gmf_data_output_id_idx on uiapi.gmf_data(output_id);
