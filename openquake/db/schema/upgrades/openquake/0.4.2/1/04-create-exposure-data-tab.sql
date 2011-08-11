/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


-- Per-asset exposure data
CREATE TABLE oqmif.exposure_data (
    id SERIAL PRIMARY KEY,
    exposure_model_id INTEGER NOT NULL,
    -- The asset reference is unique within an exposure model.
    asset_ref VARCHAR NOT NULL,
    value float NOT NULL,
    -- Vulnerability function reference
    vf_ref VARCHAR NOT NULL,
    structure_type VARCHAR,
    retrofitting_cost float,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL,
    UNIQUE (exposure_model_id, asset_ref)
) TABLESPACE oqmif_ts;
SELECT AddGeometryColumn('oqmif', 'exposure_data', 'site', 4326, 'POINT', 2);
ALTER TABLE oqmif.exposure_data ALTER COLUMN site SET NOT NULL;

ALTER TABLE oqmif.exposure_data
ADD CONSTRAINT oqmif_exposure_data_exposure_model_fk
FOREIGN KEY (exposure_model_id) REFERENCES oqmif.exposure_model(id)
ON DELETE CASCADE;

CREATE TRIGGER oqmif_exposure_data_refresh_last_update_trig BEFORE UPDATE ON oqmif.exposure_data FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();


GRANT ALL ON SEQUENCE oqmif.exposure_data_id_seq to GROUP openquake;
GRANT SELECT ON oqmif.exposure_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON oqmif.exposure_data TO oq_ged4gem;


COMMENT ON TABLE oqmif.exposure_data IS 'Per-asset risk exposure data';
COMMENT ON COLUMN oqmif.exposure_data.exposure_model_id IS 'Foreign key to the exposure model';
COMMENT ON COLUMN oqmif.exposure_data.asset_ref IS 'A unique identifier (within the exposure model) for the asset at hand';
COMMENT ON COLUMN oqmif.exposure_data.value IS 'The value of the asset at hand';
COMMENT ON COLUMN oqmif.exposure_data.vf_ref IS 'A reference to the vulnerability function that should be used for the asset at hand';
COMMENT ON COLUMN oqmif.exposure_data.structure_type IS 'An optional structure type for the asset at hand';
COMMENT ON COLUMN oqmif.exposure_data.retrofitting_cost IS 'An optional cost of retrofitting for the asset at hand';
COMMENT ON COLUMN oqmif.exposure_data.last_update IS 'Date/time of the last change of the exposure data for the asset at hand';
