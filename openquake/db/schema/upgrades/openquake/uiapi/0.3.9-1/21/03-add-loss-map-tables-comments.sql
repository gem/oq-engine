/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

COMMENT ON COLUMN uiapi.output.output_type IS 'Output type, one of:
    - unknown
    - hazard_curve
    - hazard_map
    - gmf
    - loss_curve
    - loss_map';

COMMENT ON TABLE uiapi.loss_map IS 'Holds metadata for loss maps.';
COMMENT ON COLUMN uiapi.loss_map.output_id IS 'The foreign key to the output record that represents the corresponding loss map.';
COMMENT ON COLUMN uiapi.loss_map.deterministic IS 'Is the loss map result of deterministic calculations (deterministic event-based) or not (classical psha-based or probabilistic based)';
COMMENT ON COLUMN uiapi.loss_map.loss_map_ref IS 'A simple identifier';
COMMENT ON COLUMN uiapi.loss_map.end_branch_label IS 'End branch label';
COMMENT ON COLUMN uiapi.loss_map.category IS 'Loss category (e.g. economic_loss).';
COMMENT ON COLUMN uiapi.loss_map.unit IS 'Unit of measurement';
COMMENT ON COLUMN uiapi.loss_map.poe IS 'Probability of exceedance (for probabilistic loss maps)';

COMMENT ON TABLE uiapi.loss_map_data IS 'Holds an asset, its position and a value plus (for non-deterministic maps) the standard deviation for its loss.';
COMMENT ON COLUMN uiapi.loss_map_data.loss_map_id IS 'The foreign key to the loss map';
COMMENT ON COLUMN uiapi.loss_map_data.asset_ref IS 'The asset reference';
COMMENT ON COLUMN uiapi.loss_map_data.location IS 'The position of the asset';
COMMENT ON COLUMN uiapi.loss_map_data.value IS 'The value of the loss';
COMMENT ON COLUMN uiapi.loss_map_data.std_dev IS 'The standard deviation of the loss (for deterministic maps, for non-deterministic maps the standard deviation is 0)';
