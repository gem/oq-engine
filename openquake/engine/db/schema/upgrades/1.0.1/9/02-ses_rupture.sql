ALTER TABLE hzrdr.ses_rupture RENAME old_magnitude TO magnitude;
SELECT AddGeometryColumn('hzrdr', 'ses_rupture', 'hypocenter', 4326, 'POINT', 2);

CREATE OR REPLACE FUNCTION admin.extract_magnitude (
       rupture_data BYTEA
) RETURNS FLOAT
AS $$
   import cPickle as pickle

   rupture = pickle.loads(rupture_data)

   return rupture.mag
$$ LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION admin.extract_hypocenter (
       rupture_data BYTEA
) RETURNS VARCHAR
AS $$
   import cPickle as pickle

   rupture = pickle.loads(rupture_data)

   return rupture.hypocenter.wkt2d
$$ LANGUAGE plpythonu;

UPDATE hzrdr.ses_rupture SET magnitude=admin.extract_magnitude(rupture) WHERE magnitude IS NULL;
UPDATE hzrdr.ses_rupture SET hypocenter=ST_SetSRID(admin.extract_hypocenter(rupture)::geometry, 4326);
ALTER TABLE hzrdr.ses_rupture ALTER magnitude SET NOT NULL;
ALTER TABLE hzrdr.ses_rupture ALTER hypocenter SET NOT NULL;


DROP FUNCTION admin.extract_hypocenter(BYTEA);
DROP FUNCTION admin.extract_magnitude(BYTEA);
