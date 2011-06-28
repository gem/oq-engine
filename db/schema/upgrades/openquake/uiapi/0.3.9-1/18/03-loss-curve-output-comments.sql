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

COMMENT ON TABLE uiapi.loss_asset_data IS 'Holds the asset id and its position for which loss curves were calculated.'
COMMENT ON COLUMN uiapi.loss_asset_data.output_id IS 'The foreign key to the output record that represents the corresp
COMMENT ON COLUMN uiapi.loss_asset_data.asset_id IS 'The asset id';
COMMENT ON COLUMN uiapi.loss_asset_data.pos IS 'The position of the asset';

COMMENT ON TABLE uiapi.loss_curve_data IS 'Holds the probabilities of excedeence for a given loss curve.';
COMMENT ON COLUMN uiapi.loss_curve.data.loss_asset_id IS 'The foreign key to the asset record to which the loss curve
COMMENT ON COLUMN uiapi.loss_curve.data.end_branch_label IS 'End branch label for this curve';
COMMENT ON COLUMN uiapi.loss_curve.data.abscissae IS 'The abscissae of the curve';
COMMENT ON COLUMN uiapi.loss_curve.data.poes IS 'Probabilities of exceedence';
