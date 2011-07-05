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


COMMENT ON TABLE uiapi.hazard_curve_data IS 'Holds data for hazard curves associated with a branch label';
COMMENT ON COLUMN uiapi.hazard_curve_data.output_id IS 'The foreign key to the output record that represents the corresponding hazard curve.';
COMMENT ON COLUMN uiapi.hazard_curve_data.end_branch_label IS 'End branch label for this curve.';
COMMENT ON COLUMN uiapi.hazard_curve_data.statistic_type IS 'Statistic type, one of:
    - Mean     (mean)
    - Median   (median)
    - Quantile (quantile)';
COMMENT ON COLUMN uiapi.hazard_curve_data.quantile IS 'The quantile for quantile statistical data.';
COMMENT ON COLUMN uiapi.hazard_curve_data.imls IS 'Intensity measure levels.';

COMMENT ON TABLE uiapi.hazard_curve_node_data IS 'Holds location/POE data for hazard curves';
COMMENT ON COLUMN uiapi.hazard_curve_node_data.hazard_curve_data_id IS 'The foreign key to the hazard curve record for this node.';
COMMENT ON COLUMN uiapi.hazard_curve_node_data.poes IS 'Probabilities of exceedence.';
