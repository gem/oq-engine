/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- Drop column not needed.
ALTER TABLE uiapi.output DROP COLUMN shapefile_url;

-- Make the 'truncation_level' column optional.
ALTER TABLE uiapi.oq_params ALTER COLUMN truncation_level DROP NOT NULL;
-- Add a constraint to govern when the 'truncation_level' column may be NULL.
ALTER TABLE uiapi.oq_params ADD CONSTRAINT truncation_level_is_set
CHECK(((truncation_type = 'none') AND (truncation_level IS NULL))
      OR ((truncation_type != 'none') AND (truncation_level IS NOT NULL)));
