/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- Exposure model
CREATE TABLE oqmif.exposure_model (
    id SERIAL PRIMARY KEY,
    description VARCHAR,
    -- e.g. "buildings", "bridges" etc.
    category VARCHAR NOT NULL,
    -- e.g. "EUR", "count", "density" etc.
    unit VARCHAR NOT NULL,
    last_update timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE oqmif_ts;

CREATE TRIGGER oqmif_exposure_model_refresh_last_update_trig BEFORE UPDATE ON oqmif.exposure_model FOR EACH ROW EXECUTE PROCEDURE refresh_last_update();

GRANT ALL ON SEQUENCE oqmif.exposure_model_id_seq to GROUP openquake;
GRANT SELECT ON oqmif.exposure_model TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON oqmif.exposure_model TO oq_ged4gem;

COMMENT ON TABLE oqmif.exposure_model IS 'A risk exposure model';
COMMENT ON COLUMN oqmif.exposure_model.description IS 'An optional description of the risk exposure model at hand';
COMMENT ON COLUMN oqmif.exposure_model.category IS 'The risk category modelled';
COMMENT ON COLUMN oqmif.exposure_model.unit IS 'The unit of measurement for the exposure data in the model at hand';
COMMENT ON COLUMN oqmif.exposure_model.last_update IS 'Date/time of the last change of the model at hand';
