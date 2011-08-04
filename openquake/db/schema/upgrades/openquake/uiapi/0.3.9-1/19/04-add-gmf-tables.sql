/*
    Copyright (c) 2011, GEM Foundation.

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
