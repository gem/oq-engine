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

COMMENT ON TABLE uiapi.gmf_data IS 'Holds data for the ground motion field';
COMMENT ON COLUMN uiapi.gmf_data.ground_motion IS 'Ground motion for a specific site';
COMMENT ON COLUMN uiapi.gmf_data.location IS 'Site coordinates';
