ALTER TABLE hzrdr.hazard_map ADD new_lons FLOAT[];
ALTER TABLE hzrdr.hazard_map ADD new_lats FLOAT[];
ALTER TABLE hzrdr.hazard_map ADD new_imls FLOAT[];

CREATE OR REPLACE FUNCTION admin.numpy_to_pg(
       arr BYTEA
) RETURNS FLOAT[]
AS $$
    import cPickle as pickle
    return pickle.loads(arr)
$$ LANGUAGE plpythonu;

UPDATE hzrdr.hazard_map SET new_lons=admin.numpy_to_pg(lons);
UPDATE hzrdr.hazard_map SET new_lats=admin.numpy_to_pg(lats);
UPDATE hzrdr.hazard_map SET new_imls=admin.numpy_to_pg(imls);

ALTER TABLE hzrdr.hazard_map ALTER new_lons SET NOT NULL;
ALTER TABLE hzrdr.hazard_map ALTER new_lats SET NOT NULL;
ALTER TABLE hzrdr.hazard_map ALTER new_imls SET NOT NULL;

ALTER TABLE hzrdr.hazard_map DROP lons;
ALTER TABLE hzrdr.hazard_map DROP lats;
ALTER TABLE hzrdr.hazard_map DROP imls;

ALTER TABLE hzrdr.hazard_map RENAME new_lons TO lons;
ALTER TABLE hzrdr.hazard_map RENAME new_lats TO lats;
ALTER TABLE hzrdr.hazard_map RENAME new_imls TO imls;

DROP FUNCTION admin.numpy_to_pg(BYTEA);
