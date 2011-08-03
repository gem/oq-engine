/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

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
