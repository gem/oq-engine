/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


-- Benefit-cost ratio distribution
CREATE TABLE riskr.bcr_distribution (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL, -- FK to output.id
    exposure_model_id INTEGER NOT NULL -- FK to exposure_model.id
) TABLESPACE riskr_ts;

CREATE TABLE riskr.bcr_distribution_data (
    id SERIAL PRIMARY KEY,
    bcr_distribution_id INTEGER NOT NULL, -- FK to bcr_distribution.id
    asset_ref VARCHAR NOT NULL,
    bcr float NOT NULL CONSTRAINT bcr_value
        CHECK (bcr >= 0.0)
) TABLESPACE riskr_ts;
SELECT AddGeometryColumn('riskr', 'bcr_distribution_data', 'location', 4326, 'POINT', 2);
ALTER TABLE riskr.bcr_distribution_data ALTER COLUMN location SET NOT NULL;


-- foreign keys
ALTER TABLE riskr.bcr_distribution
ADD CONSTRAINT riskr_bcr_distribution_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE riskr.bcr_distribution
ADD CONSTRAINT riskr_bcr_distribution_exposure_model_fk
FOREIGN KEY (exposure_model_id) REFERENCES oqmif.exposure_model(id) ON DELETE RESTRICT;

ALTER TABLE riskr.bcr_distribution_data
ADD CONSTRAINT riskr_bcr_distribution_data_bcr_distribution_fk
FOREIGN KEY (bcr_distribution_id) REFERENCES riskr.bcr_distribution(id) ON DELETE CASCADE;
