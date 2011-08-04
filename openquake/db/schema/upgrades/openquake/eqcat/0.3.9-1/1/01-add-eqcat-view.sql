/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/
-- global catalog view, needed for Geonode integration
CREATE VIEW eqcat.catalog_allfields AS
SELECT
    eqcat.catalog.*,
    eqcat.surface.semi_minor, eqcat.surface.semi_major,
    eqcat.surface.strike,
    eqcat.magnitude.mb_val, eqcat.magnitude.mb_val_error,
    eqcat.magnitude.ml_val, eqcat.magnitude.ml_val_error,
    eqcat.magnitude.ms_val, eqcat.magnitude.ms_val_error,
    eqcat.magnitude.mw_val, eqcat.magnitude.mw_val_error
FROM eqcat.catalog, eqcat.magnitude, eqcat.surface
WHERE
    eqcat.catalog.magnitude_id = eqcat.magnitude.id
    AND eqcat.catalog.surface_id = eqcat.surface.id;

COMMENT ON VIEW eqcat.catalog_allfields IS 'A global catalog view, needed       
for geonode integration';
