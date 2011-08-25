/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


-- Collapse map data.
CREATE TABLE riskr.collapse_map (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    exposure_model_id INTEGER NOT NULL -- FK to exposure_model.id
) TABLESPACE riskr_ts;

CREATE TABLE riskr.collapse_map_data (
    id SERIAL PRIMARY KEY,
    collapse_map_id INTEGER NOT NULL, -- FK to collapse_map.id
    asset_ref VARCHAR NOT NULL,
    value float NOT NULL,
    std_dev float NOT NULL
) TABLESPACE riskr_ts;
SELECT AddGeometryColumn('riskr', 'collapse_map_data', 'location', 4326, 'POINT', 2);
ALTER TABLE riskr.collapse_map_data ALTER COLUMN location SET NOT NULL;


-- foreign keys
ALTER TABLE riskr.collapse_map
ADD CONSTRAINT riskr_collapse_map_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.collapse_map
ADD CONSTRAINT riskr_collapse_map_exposure_model_fk
FOREIGN KEY (exposure_model_id) REFERENCES oqmif.exposure_model(id) ON DELETE RESTRICT;

ALTER TABLE riskr.collapse_map_data
ADD CONSTRAINT riskr_collapse_map_data_collapse_map_fk
FOREIGN KEY (collapse_map_id) REFERENCES riskr.collapse_map(id) ON DELETE CASCADE;


-- indices
CREATE INDEX riskr_collapse_map_output_id_idx on riskr.collapse_map(output_id);
CREATE INDEX riskr_collapse_map_data_collapse_map_id_idx on riskr.collapse_map_data(collapse_map_id);


-- comments
COMMENT ON TABLE riskr.collapse_map IS 'Holds metadata for the collapse map';
COMMENT ON COLUMN riskr.collapse_map.output_id IS 'The foreign key to the output record that represents the corresponding collapse map.';
COMMENT ON COLUMN riskr.collapse_map.exposure_model_id IS 'The foreign key to the exposure model for this collapse map.';

COMMENT ON TABLE riskr.collapse_map_data IS 'Holds the actual data for the collapse map';
COMMENT ON COLUMN riskr.collapse_map_data.collapse_map_id IS 'The foreign key to the map record to which the collapse map data belongs';
COMMENT ON COLUMN riskr.collapse_map_data.asset_ref IS 'The asset id';
COMMENT ON COLUMN riskr.collapse_map_data.value IS 'The collapse amount';
COMMENT ON COLUMN riskr.collapse_map_data.std_dev IS 'The standard deviation of the collapse amount';


-- grants
GRANT ALL ON SEQUENCE riskr.collapse_map_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE riskr.collapse_map_id_seq to GROUP openquake;

GRANT SELECT ON riskr.collapse_map TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.collapse_map TO oq_reslt_writer;

GRANT SELECT ON riskr.collapse_map_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON riskr.collapse_map_data TO oq_reslt_writer;

