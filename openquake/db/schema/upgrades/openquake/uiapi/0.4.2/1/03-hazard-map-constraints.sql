/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- add hazard_map_data FK
ALTER TABLE uiapi.hazard_map_data
ADD CONSTRAINT uiapi_hazard_map_data_hazard_map_fk
FOREIGN KEY (hazard_map_id) REFERENCES uiapi.hazard_map(id) ON DELETE CASCADE;
