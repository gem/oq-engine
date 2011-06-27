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


-- Hazard curve data.
CREATE TABLE uiapi.hazard_curve_data (
    id SERIAL PRIMARY KEY,
    output_id INTEGER NOT NULL,
    -- Realization reference string
    end_branch_label VARCHAR CONSTRAINT end_branch_label_value
        CHECK(
            ((end_branch_label IS NULL) AND (statistic_type IS NOT NULL))
            OR ((end_branch_label IS NOT NULL) AND (statistic_type IS NULL))),
    -- Statistic type, one of:
    --      mean
    --      median
    --      quantile
    statistic_type VARCHAR CONSTRAINT statistic_type_value
        CHECK(statistic_type IS NULL OR
              statistic_type IN ('mean', 'median', 'quantile')),
    -- Quantile value (only for "quantile" statistics)
    quantile float CONSTRAINT quantile_value
        CHECK(
            ((statistic_type = 'quantile') AND (quantile IS NOT NULL))
            OR (((statistic_type <> 'quantile') AND (quantile IS NULL)))),
    -- Intensity measure levels
    imls float[] NOT NULL
) TABLESPACE uiapi_ts;


-- Hazard curve node data.
CREATE TABLE uiapi.hazard_curve_node_data (
    id SERIAL PRIMARY KEY,
    hazard_curve_data_id INTEGER NOT NULL,
    -- Probabilities of exceedence
    poes float[] NOT NULL
) TABLESPACE uiapi_ts;
SELECT AddGeometryColumn('uiapi', 'hazard_curve_node_data', 'location', 4326, 'POINT', 2);
ALTER TABLE uiapi.hazard_curve_node_data ALTER COLUMN location SET NOT NULL;

-- Foreign keys
ALTER TABLE uiapi.hazard_curve_data
ADD CONSTRAINT uiapi_hazard_curve_data_output_fk
FOREIGN KEY (output_id) REFERENCES uiapi.output(id) ON DELETE CASCADE;

ALTER TABLE uiapi.hazard_curve_node_data
ADD CONSTRAINT uiapi_hazard_curve_node_data_output_fk
FOREIGN KEY (hazard_curve_data_id) REFERENCES uiapi.hazard_curve_data(id) ON DELETE CASCADE;

-- Indices
CREATE INDEX uiapi_hazard_curve_data_output_id_idx on uiapi.hazard_curve_data(output_id);
CREATE INDEX uiapi_hazard_curve_node_data_hazard_curve_data_id_idx on uiapi.hazard_curve_node_data(hazard_curve_data_id);
