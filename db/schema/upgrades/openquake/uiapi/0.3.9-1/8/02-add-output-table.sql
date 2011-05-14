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

-- add the uiapi.output table (holds information pertaining to a single
-- OpenQuake calculation engine output file).

-- A single OpenQuake calculation engine output file.
CREATE TABLE uiapi.output (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    oq_job_id INTEGER NOT NULL,
    -- The full path of the output file on the server
    path VARCHAR NOT NULL UNIQUE,
    -- Output file type, one of:
    --      hazard_curve
    --      hazard_map
    --      loss_curve
    --      loss_map
    output_type VARCHAR NOT NULL CONSTRAINT output_type_value
        CHECK(output_type IN ('unknown', 'hazard_curve', 'hazard_map',
            'loss_curve', 'loss_map')),
    -- Number of bytes in file
    size INTEGER NOT NULL DEFAULT 0,
    -- The full path of the shapefile generated for a hazard or loss map.
    shapefile_path VARCHAR,
    -- The geonode URL of the shapefile generated for a hazard or loss map.
    shapefile_url VARCHAR,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;


ALTER TABLE uiapi.output ADD CONSTRAINT uiapi_output_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE RESTRICT;

ALTER TABLE uiapi.output ADD CONSTRAINT uiapi_output_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

-- uiapi.output
GRANT SELECT ON uiapi.output TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.output TO oq_uiapi_writer;

COMMENT ON TABLE uiapi.output IS 'A single OpenQuake calculation engine output file.';
COMMENT ON COLUMN uiapi.output.output_type IS 'Output file type, one of:
    - unknown
    - hazard_curve
    - hazard_map
    - loss_curve
    - loss_map';
COMMENT ON COLUMN uiapi.output.shapefile_path IS 'The full path of the shapefile generated for a hazard or loss map.';
COMMENT ON COLUMN uiapi.output.shapefile_url IS 'The geonode URL of the shapefile generated for a hazard or loss map.';
COMMENT ON COLUMN uiapi.output.path IS 'The full path of the output file on the server.';
