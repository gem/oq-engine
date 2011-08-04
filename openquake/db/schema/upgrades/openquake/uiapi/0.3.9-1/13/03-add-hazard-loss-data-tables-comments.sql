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

COMMENT ON TABLE uiapi.hazard_map_data IS 'Holds location/IML data for hazard maps';
COMMENT ON COLUMN uiapi.hazard_map_data.output_id IS 'The foreign key to the output record that represents the corresponding hazard map.';


COMMENT ON TABLE uiapi.loss_map_data IS 'Holds location/loss data for loss maps.';
COMMENT ON COLUMN uiapi.loss_map_data.output_id IS 'The foreign key to the output record that represents the corresponding loss map.';
