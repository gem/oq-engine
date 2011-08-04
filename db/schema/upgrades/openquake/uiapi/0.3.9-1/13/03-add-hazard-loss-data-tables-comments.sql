/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

COMMENT ON TABLE uiapi.hazard_map_data IS 'Holds location/IML data for hazard maps';
COMMENT ON COLUMN uiapi.hazard_map_data.output_id IS 'The foreign key to the output record that represents the corresponding hazard map.';


COMMENT ON TABLE uiapi.loss_map_data IS 'Holds location/loss data for loss maps.';
COMMENT ON COLUMN uiapi.loss_map_data.output_id IS 'The foreign key to the output record that represents the corresponding loss map.';
