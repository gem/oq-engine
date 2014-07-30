/* some forgotten comments */

COMMENT ON TABLE hzrdi.hazard_site IS 'A collection of hazard curves. This table defines common attributes for the collection.';
COMMENT ON COLUMN hzrdi.hazard_site.hazard_calculation_id IS 'Foreign key to the corresponding hazard_calculation';
COMMENT ON COLUMN hzrdi.hazard_site.location IS 'Geography point corresponding to the given site';
