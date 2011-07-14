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

-- new output type

ALTER TABLE uiapi.output DROP CONSTRAINT output_type_value;

ALTER TABLE uiapi.output ADD CONSTRAINT output_type_value
        CHECK(output_type IN ('unknown', 'hazard_curve', 'hazard_map',
            'gmf', 'loss_curve', 'loss_map'));

COMMENT ON COLUMN uiapi.output.output_type IS 'Output type, one of:
    - unknown
    - hazard_curve
    - hazard_map
    - gmf
    - loss_curve
    - loss_map';

-- Loss curve.
CREATE TABLE uiapi.loss_curve (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,

    end_branch_label VARCHAR,
    category VARCHAR,
    unit VARCHAR -- e.g. EUR, USD
) TABLESPACE uiapi_ts;

-- Loss curve data. Holds the asset, its position and value plus the calculated curve.
CREATE TABLE uiapi.loss_curve_data (
    id SERIAL PRIMARY KEY,
    loss_curve_id INTEGER NOT NULL,

    asset_ref VARCHAR NOT NULL,
    asset_value float NOT NULL,
    -- Loss ratios
    ratios float[] NOT NULL CONSTRAINT valid_ratios CHECK (0 <= ALL(ratios) AND 1 >= ALL(ratios)),
    -- Probabilities of exceedence
    poes float[] NOT NULL
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'loss_curve_data', 'location', 4326, 'POINT', 2);
ALTER TABLE uiapi.loss_curve_data ALTER COLUMN location SET NOT NULL;

CREATE INDEX uiapi_loss_curve_output_id_idx on uiapi.loss_curve(output_id);
CREATE INDEX uiapi_loss_curve_data_loss_curve_id_idx on uiapi.loss_curve_data(loss_curve_id);

ALTER TABLE uiapi.loss_curve
ADD CONSTRAINT uiapi_loss_curve_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE uiapi.loss_curve_data
ADD CONSTRAINT uiapi_loss_curve_data_loss_curve_fk
FOREIGN KEY (loss_curve_id) REFERENCES uiapi.loss_curve(id) ON DELETE CASCADE;

-- security
GRANT ALL ON SEQUENCE uiapi.loss_curve_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.loss_curve_data_id_seq to GROUP openquake;

-- uiapi.loss_curve
GRANT SELECT ON uiapi.loss_curve TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.loss_curve TO oq_uiapi_writer;

-- uiapi.loss_curve_data
GRANT SELECT ON uiapi.loss_curve_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.loss_curve_data TO oq_uiapi_writer;

-- comments
COMMENT ON TABLE uiapi.loss_curve IS 'Holds the parameters common to a set of loss curves.';
COMMENT ON COLUMN uiapi.loss_curve.output_id IS 'The foreign key to the output record that represents the corresponding loss curve.';
COMMENT ON COLUMN uiapi.loss_curve.end_branch_label IS 'End branch label';
COMMENT ON COLUMN uiapi.loss_curve.category IS 'The category of the losses';
COMMENT ON COLUMN uiapi.loss_curve.unit IS 'Unit for the losses (e.g. currency)';

COMMENT ON TABLE uiapi.loss_curve_data IS 'Holds the probabilities of excedeence for a given loss curve.';
COMMENT ON COLUMN uiapi.loss_curve_data.loss_curve_id IS 'The foreign key to the curve record to which the loss curve data belongs';
COMMENT ON COLUMN uiapi.loss_curve_data.asset_ref IS 'The asset id';
COMMENT ON COLUMN uiapi.loss_curve_data.asset_value IS 'The value of the asset';
COMMENT ON COLUMN uiapi.loss_curve_data.location IS 'The position of the asset';
COMMENT ON COLUMN uiapi.loss_curve_data.ratios IS 'Loss ratios (0 <= loss <= 1)';
COMMENT ON COLUMN uiapi.loss_curve_data.poes IS 'Probabilities of exceedence';
