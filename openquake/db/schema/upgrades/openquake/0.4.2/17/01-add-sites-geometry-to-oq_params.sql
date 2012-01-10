/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


-- schema changes:

-- Remove NOT NULL constraints from region and region_grid_spacing:
ALTER TABLE uiapi.oq_job_profile ALTER COLUMN region DROP NOT NULL;
ALTER TABLE uiapi.oq_job_profile ALTER COLUMN region_grid_spacing DROP NOT NULL;

-- Add the 'sites' column to oq_job_profile:
SELECT AddGeometryColumn('uiapi', 'oq_job_profile', 'sites', 4326, 'MULTIPOINT', 2);
-- Params can either contain a site list ('sites') or
-- region + region_grid_spacing, but not both.
ALTER TABLE uiapi.oq_job_profile ADD CONSTRAINT oq_job_profile_geometry CHECK(
    ((region IS NOT NULL) AND (region_grid_spacing IS NOT NULL)
        AND (sites IS NULL))
    OR ((region IS NULL) AND (region_grid_spacing IS NULL)
        AND (sites IS NOT NULL)));


-- comments:
COMMENT ON COLUMN uiapi.oq_job_profile.region IS 'Region of interest for the calculation (Polygon)';
COMMENT ON COLUMN uiapi.oq_job_profile.region_grid_spacing IS 'Desired cell size (in degrees), used when splitting up the region of interest. This effectively defines the resolution of the calculation. (Smaller grid spacing means more sites and thus more calculations.)';
COMMENT ON COLUMN uiapi.oq_job_profile.sites IS 'Sites of interest for the calculation (MultiPoint)';

