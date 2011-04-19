INSERT INTO pshai.mfd_tgr(owner_id, gid, magnitude_type_id, min_val, max_val, a_val, b_val) VALUES(1, 'mfd_tgr/1', 1, 2.0, 3.0, 4.0, 5.0);

INSERT INTO pshai.simple_fault(owner_id, gid, dip, upper_depth, lower_depth, geom, mfd_tgr_id) VALUES (1, 'sgeo_1', 22.0, 77.0, 55.0, ST_GeomFromEWKT('SRID=4326;LINESTRING(-80 28,-90 29)'), 1);

INSERT INTO pshai.rupture(owner_id, gid, tectonic_region_id, rake, magnitude, magnitude_type_id, simple_fault_id) VALUES(1, 'rupture/1', 1, 11.0, 7.6, 1, 1);

INSERT INTO pshai.rupture(owner_id, gid, tectonic_region_id, rake, magnitude, magnitude_type_id, simple_fault_id, point) VALUES(1, 'rupture/1', 1, 11.0, 7.6, 1, 3, ST_GeomFromEWKT('SRID=4326;POINT(-80 28 0)'));

UPDATE pshai.rupture SET point=ST_GeomFromEWKT('SRID=4326;POINT(-80 28 0)') WHERE id=1;

INSERT INTO pshai.source(owner_id, gid, tectonic_region_id, rake, simple_fault_id) VALUES(1, 'rupture/1', 1, 11.0, 1);
INSERT INTO pshai.source(owner_id, gid, tectonic_region_id, rake, simple_fault_id, point) VALUES(1, 'rupture/1', 1, 11.0, 1, ST_GeomFromEWKT('SRID=4326;POINT(-80 28)'));
UPDATE pshai.source SET point=ST_GeomFromEWKT('SRID=4326;POINT(-80 28)') WHERE id=1;

INSERT INTO pshai.mfd_evd(owner_id, gid, magnitude_type_id, min_val, bin_size, mfd_values) VALUES(1, 'mfd_evd/1', 1, 1.0, 2.0, ARRAY[3.0, 4.0, 5.0]);

INSERT INTO pshai.focal_mechanism(owner_id, gid, strike, dip, rake) VALUES(1, 'focal_mechanism/1', 359.0, 89.0, 179.0);

INSERT INTO pshai.r_rate_mdl(owner_id, gid, mfd_tgr_id, focal_mechanism_id) VALUES(1, 'r_rate_mdl/1', 1, 1);

UPDATE pshai.r_rate_mdl SET mfd_evd_id=1 WHERE id=1;

INSERT INTO pshai.simple_fault(owner_id, gid, dip, upper_depth, lower_depth, geom, mfd_tgr_id, mfd_evd_id) VALUES (1, 'sgeo_1', 22.0, 77.0, 55.0, ST_GeomFromEWKT('SRID=4326;LINESTRING(-80 28,-90 29)'), 1, 1);

UPDATE pshai.simple_fault SET mfd_evd_id=1 WHERE id=1;
