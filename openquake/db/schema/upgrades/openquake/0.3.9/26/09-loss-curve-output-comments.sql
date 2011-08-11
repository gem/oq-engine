/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

COMMENT ON TABLE uiapi.loss_asset_data IS 'Holds the asset id and its position for which loss curves were calculated.';
COMMENT ON COLUMN uiapi.loss_asset_data.output_id IS 'The foreign key to the output record that represents the corresponding loss curve.';
COMMENT ON COLUMN uiapi.loss_asset_data.asset_id IS 'The asset id';
COMMENT ON COLUMN uiapi.loss_asset_data.pos IS 'The position of the asset';

COMMENT ON TABLE uiapi.loss_curve_data IS 'Holds the probabilities of exceedance for a given loss curve.';
COMMENT ON COLUMN uiapi.loss_curve_data.loss_asset_id IS 'The foreign key to the asset record to which the loss curve belongs';
COMMENT ON COLUMN uiapi.loss_curve_data.end_branch_label IS 'End branch label for this curve';
COMMENT ON COLUMN uiapi.loss_curve_data.abscissae IS 'The abscissae of the curve';
COMMENT ON COLUMN uiapi.loss_curve_data.poes IS 'Probabilities of exceedence';

