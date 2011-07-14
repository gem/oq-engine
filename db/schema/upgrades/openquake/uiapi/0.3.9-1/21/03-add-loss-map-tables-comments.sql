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

COMMENT ON COLUMN uiapi.output.output_type IS 'Output type, one of:
    - unknown
    - hazard_curve
    - hazard_map
    - gmf
    - loss_curve
    - loss_map';

COMMENT ON TABLE uiapi.loss_map IS 'Holds metadata for loss maps.';
COMMENT ON COLUMN uiapi.loss_map.output_id IS 'The foreign key to the output record that represents the corresponding loss map.';
COMMENT ON COLUMN uiapi.loss_map.loss_map_type IS 'The type of this loss map, one of:
    - probabilistic (classical psha-based or probabilistic based calculations)
    - deterministic (deterministic event-based calculations)';
COMMENT ON COLUMN uiapi.loss_map.loss_map_ref IS 'A simple identifier';
COMMENT ON COLUMN uiapi.loss_map.end_branch_label IS 'End branch label';
COMMENT ON COLUMN uiapi.loss_map.category IS 'Loss category (e.g. economic_loss).';
COMMENT ON COLUMN uiapi.loss_map.unit IS 'Monetary unit (one of EUR, USD)';
COMMENT ON COLUMN uiapi.loss_map.poe IS 'Probability of exceedance (for probabilistic loss maps)';

COMMENT ON TABLE uiapi.loss_map_data IS 'Holds an asset, its position and either a value or a mean plus standard deviation for its loss.';
COMMENT ON COLUMN uiapi.loss_map_data.loss_map_id IS 'The foreign key to the loss map';
COMMENT ON COLUMN uiapi.loss_map_data.asset_ref IS 'The asset reference';
COMMENT ON COLUMN uiapi.loss_map_data.site IS 'The site of the asset';
COMMENT ON COLUMN uiapi.loss_map_data.mean IS 'The mean loss (for deterministic maps)';
COMMENT ON COLUMN uiapi.loss_map_data.std_dev IS 'The standard deviation of the loss (for deterministic maps)';
COMMENT ON COLUMN uiapi.loss_map_data.value IS 'The value of the loss (for probabilistic maps)';
