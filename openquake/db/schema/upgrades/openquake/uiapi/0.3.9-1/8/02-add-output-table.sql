/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

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
    -- The min/max value is only needed for hazard/loss maps (for the
    -- generation of the relative color scale)
    min_value float,
    max_value float,
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
