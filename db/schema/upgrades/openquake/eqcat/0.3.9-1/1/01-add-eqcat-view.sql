
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
FROM
    eqcat.catalog
JOIN eqcat.magnitude ON eqcat.catalog.magnitude_id = eqcat.magnitude.id
JOIN eqcat.surface ON eqcat.catalog.surface_id = eqcat.surface.id;
