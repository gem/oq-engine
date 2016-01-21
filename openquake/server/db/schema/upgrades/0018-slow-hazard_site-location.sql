ALTER TABLE hzrdi.hazard_site ADD COLUMN lon FLOAT;
ALTER TABLE hzrdi.hazard_site ADD COLUMN lat FLOAT;

COMMENT ON COLUMN hzrdi.hazard_site.lon IS 'longitude';
COMMENT ON COLUMN hzrdi.hazard_site.lat IS 'latitude';

UPDATE hzrdi.hazard_site SET lon = ST_X(location::GEOMETRY);
UPDATE hzrdi.hazard_site SET lat = ST_Y(location::GEOMETRY);

ALTER TABLE hzrdi.hazard_site DROP COLUMN location;
