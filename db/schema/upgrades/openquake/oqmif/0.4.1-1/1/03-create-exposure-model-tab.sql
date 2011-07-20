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
