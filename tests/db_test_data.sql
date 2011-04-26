-- SETUP
INSERT INTO pshai.focal_mechanism(owner_id, gid, strike, dip, rake) VALUES(1, 'focal_mechanism/1', 351.0, 81.0, 171.0);
INSERT INTO pshai.focal_mechanism(owner_id, gid, strike, dip, rake) VALUES(1, 'focal_mechanism/2', 359.0, 89.0, 179.0);

INSERT INTO pshai.mfd_evd(owner_id, gid, magnitude_type_id, min_val, bin_size, mfd_values) VALUES(1, 'mfd_evd/1', 1, 1.0, 2.0, ARRAY[3.0, 4.0, 5.0]);

INSERT INTO pshai.mfd_tgr(owner_id, gid, magnitude_type_id, min_val, max_val, a_val, b_val) VALUES(1, 'mfd_tgr/1', 1, 2.0, 3.0, 4.0, 5.0);

INSERT INTO pshai.simple_fault(owner_id, gid, dip, upper_depth, lower_depth, geom, mfd_tgr_id) VALUES (1, 'sfault/1', 22.0, 77.0, 55.0, ST_GeomFromEWKT('SRID=4326;LINESTRING(-80 28 11,-90 29 9)'), 1);

INSERT INTO pshai.rupture(owner_id, gid, tectonic_region_id, rake, magnitude, magnitude_type_id, simple_fault_id) VALUES(1, 'rupture/1', 1, 11.0, 7.6, 1, 1);

INSERT INTO pshai.source(owner_id, gid, tectonic_region_id, rake, simple_fault_id) VALUES(1, 'source/1', 1, 11.0, 1);

INSERT INTO pshai.fault_edge(owner_id, gid, top, bottom) VALUES (1, 'fedge/sa/ca/1', ST_GeomFromEWKT('SRID=4326;LINESTRING(-120.461303711 35.9206581116 0.0, -120.462242126 35.9214630127 0.0, -120.462997437 35.9219589233 0.0, -120.463157654 35.9221496582 0.0, -120.463905334 35.9226875305 0.0, -120.465263367 35.9240570068 0.0, -120.466148376 35.9249572754 0.0, -120.466781616 35.9255218506 0.0, -120.467506409 35.9260063171 0.0, -120.468315125 35.9265556335 0.0, -120.468963623 35.9270782471 0.0, -120.469696045 35.9276847839 0.0, -120.469978333 35.9279708862 0.0, -120.470245361 35.9282913208 0.0, -120.470916748 35.9289436340 0.0, -120.471824646 35.9299125671 0.0, -120.472145081 35.9302787781 0.0, -120.472526550 35.9305877686 0.0, -120.473251343 35.9311904907 0.0, -120.474563599 35.9323844910 0.0)'), ST_GeomFromEWKT('SRID=4326;LINESTRING(-120.528236389 35.9759864807 1.87, -120.528327942 35.9760551453 1.87, -120.528457642 35.9761276245 1.87, -120.528625488 35.9762077332 1.87, -120.528732300 35.9762687683 1.87, -120.528808594 35.9763259888 1.87, -120.528892517 35.9764175415 1.87, -120.528976440 35.9765510559 1.87, -120.529029846 35.9766464233 1.87, -120.529129028 35.9767761230 1.87, -120.529235840 35.9769020081 1.87, -120.529350281 35.9770011902 1.87, -120.529510498 35.9771270752 1.87, -120.529640198 35.9772224426 1.87, -120.529785156 35.9773674011 1.87)'));

INSERT INTO pshai.complex_fault(owner_id, gid, mfd_evd_id, fault_edge_id) VALUES (1, 'cfault/sa/ca/1', 1, 4);

INSERT INTO pshai.source(owner_id, gid, si_type, tectonic_region, complex_fault_id) VALUES (1, 'complex-source/sa/ca/10', 'complex', 'active', 10);

INSERT INTO pshai.r_rate_mdl(owner_id, gid, mfd_tgr_id, focal_mechanism_id, source_id) VALUES(1, 'r_rate_mdl/1', 1, 1, 1);

INSERT INTO pshai.r_depth_distr(owner_id, gid, magnitude, depth) VALUES(1, 'r_depth_distr/1', '{1.0, 2.0}', '{3.0, 4.0}');

INSERT INTO pshai.source(owner_id, gid, tectonic_region_id, rake, point, hypocentral_depth, r_depth_distr_id, si_type) VALUES(1, 'source/8', 1, 11.0, ST_GeomFromEWKT('SRID=4326;POINT(-80 28)'), 79.0, 1, 'point');

INSERT INTO eqcat.magnitude(mw_val) VALUES(7.6);
INSERT INTO eqcat.surface(semi_minor, semi_major, strike) VALUES(1.01, 2.43, 298);
INSERT INTO eqcat.catalog(owner_id, eventid, agency, identifier, time, time_error, depth, depth_error, magnitude_id, surface_id, point) VALUES (1, 2, 'AAA', '20000105132157', now(), 11.23, 44.318, 0.77, 1, 1, ST_GeomFromEWKT('SRID=4326;POINT(-80 28)'));

INSERT INTO pshai.source(owner_id, gid, si_type, tectonic_region, hypocentral_depth, r_depth_distr_id, area) VALUES (1, 'area-source/1', 'area', 'active', 1.1, 1, ST_GeomFromEWKT('SRID=4326;POLYGON((-120.416267395 35.8784446716, -120.419479370 35.8811035156, -120.422492981 35.8836975098, -120.425315857 35.8864784241, -120.427146912 35.8882675171, -120.416267395 35.8784446716))'));

INSERT INTO pshai.simple_fault(owner_id, gid, dip, upper_depth, lower_depth, mfd_tgr_id, geom) VALUES (1, 'sfault/sa/ca/1', 22.0, 77.0, 55.0, 1, ST_GeomFromEWKT('SRID=4326;LINESTRING(-120.427154541 35.8882789612 0.0, -120.427444458 35.8886375427 0.0, -120.427772522 35.8890228271 0.0, -120.428138733 35.8895149231 0.0, -120.428367615 35.8898086548 0.0, -120.428634644 35.8900680542 0.0, -120.429069519 35.8903884888 0.0, -120.429527283 35.8906517029 0.0, -120.430030823 35.8909835815 0.0, -120.430473328 35.8912582397 0.0, -120.431053162 35.8917007446 0.0, -120.431449890 35.8920516968 0.0, -120.431922913 35.8925056458 0.0, -120.432495117 35.8929824829 0.0, -120.433471680 35.8938980103 0.0, -120.433784485 35.8942146301 0.0)'));

INSERT INTO pshai.source(owner_id, gid, si_type, tectonic_region, simple_fault_id) VALUES (1, 'simple-source/sa/ca/10', 'simple', 'active', 10);

-- TEST
-- Failure due to duplicate source (point)
INSERT INTO pshai.rupture(owner_id, gid, tectonic_region_id, rake, magnitude, magnitude_type_id, simple_fault_id, point) VALUES(1, 'rupture/2', 1, 11.0, 7.6, 1, 1, ST_GeomFromEWKT('SRID=4326;POINT(-80 28 0)'));

-- Failure due to duplicate source (point)
UPDATE pshai.rupture SET point=ST_GeomFromEWKT('SRID=4326;POINT(-80 28 0)') WHERE id=1;

-- Failure due to duplicate source (point)
INSERT INTO pshai.source(owner_id, gid, tectonic_region_id, rake, simple_fault_id, point) VALUES(1, 'source/2', 1, 11.0, 1, ST_GeomFromEWKT('SRID=4326;POINT(-80 28)'));

-- Failure due to duplicate source (point)
UPDATE pshai.source SET point=ST_GeomFromEWKT('SRID=4326;POINT(-80 28)') WHERE id=1;
-- Failure due to duplicate source (complex fault)
UPDATE pshai.source SET complex_fault_id=1 WHERE id=1;

-- Failure due to duplicate magnitude frequency distribution
INSERT INTO pshai.r_rate_mdl(owner_id, gid, mfd_tgr_id, focal_mechanism_id, mfd_evd_id) VALUES(1, 'r_rate_mdl/2', 1, 1, 1);

-- Failure due to duplicate magnitude frequency distribution
UPDATE pshai.r_rate_mdl SET mfd_evd_id=1 WHERE id=1;

-- Failure due to duplicate source (point)
INSERT INTO pshai.simple_fault(owner_id, gid, dip, upper_depth, lower_depth, geom, mfd_tgr_id, mfd_evd_id) VALUES (1, 'sfault/2', 22.0, 77.0, 55.0, ST_GeomFromEWKT('SRID=4326;LINESTRING(-80 28 0,-90 29 1)'), 1, 1);

-- Failure due to duplicate source (point)
UPDATE pshai.simple_fault SET mfd_evd_id=1 WHERE id=1;

-- Failure due to duplicate magnitude frequency distribution
INSERT INTO pshai.complex_fault(owner_id, gid, mfd_evd_id, fault_edge_id, mfd_tgr_id) VALUES (1, 'cfault/2', 1, 1, 1);
-- Failure due to duplicate magnitude frequency distribution
UPDATE pshai.complex_fault SET mfd_tgr_id=1 WHERE id=1;

-- Failure due to missing magnitude frequency distribution
INSERT INTO pshai.simple_fault(owner_id, gid, dip, upper_depth, lower_depth, geom) VALUES (1, 'sfault/1', 22.0, 77.0, 55.0, ST_GeomFromEWKT('SRID=4326;LINESTRING(-80 28 13,-90 29 12)'));
INSERT INTO pshai.complex_fault(owner_id, gid, fault_edge_id) VALUES (1, 'cfault/1', 1);
UPDATE pshai.complex_fault SET mfd_evd_id=NULL WHERE id=1;

-- Failure due to missing source/input
INSERT INTO pshai.source(owner_id, gid, tectonic_region_id, rake)  VALUES(1, 'source/3', 1, 11.0);
INSERT INTO pshai.rupture(owner_id, gid, tectonic_region_id, rake, magnitude, magnitude_type_id)  VALUES(1, 'rupture/3', 1, 11.0, 7.6, 1);
UPDATE pshai.source SET simple_fault_id=NULL WHERE id=1;
UPDATE pshai.rupture SET simple_fault_id=NULL WHERE id=1;

-- Failure due to superfluous hypocentral_depth/r_depth_distr_id
INSERT INTO pshai.source(owner_id, gid, tectonic_region_id, rake, simple_fault_id, hypocentral_depth) VALUES(1, 'source/4', 1, 11.0, 1, 99.0);
INSERT INTO pshai.source(owner_id, gid, tectonic_region_id, rake, simple_fault_id, r_depth_distr_id) VALUES(1, 'source/5', 1, 11.0, 1, 1);
UPDATE pshai.source SET hypocentral_depth=1.1 WHERE id=1;
UPDATE pshai.source SET r_depth_distr_id=1 WHERE id=1;

-- Failure due to superfluous hypocentral_depth/r_depth_distr_id
INSERT INTO pshai.source(owner_id, gid, tectonic_region_id, rake, simple_fault_id, hypocentral_depth) VALUES(1, 'source/6', 1, 11.0, 1, 99.0);
INSERT INTO pshai.source(owner_id, gid, tectonic_region_id, rake, simple_fault_id, r_depth_distr_id) VALUES(1, 'source/7', 1, 11.0, 1, 1);
UPDATE pshai.source SET hypocentral_depth=1.1 WHERE id=1;
UPDATE pshai.source SET r_depth_distr_id=1 WHERE id=1;

-- Failure due to missing hypocentral_depth/r_depth_distr_id
INSERT INTO pshai.source(owner_id, gid, tectonic_region_id, rake, point, r_depth_distr_id) VALUES(1, 'source/8', 1, 11.0, ST_GeomFromEWKT('SRID=4326;POINT(-80 28)'), 1);
INSERT INTO pshai.source(owner_id, gid, tectonic_region_id, rake, point, hypocentral_depth) VALUES(1, 'source/8', 1, 11.0, ST_GeomFromEWKT('SRID=4326;POINT(-80 28)'), 79.0);
UPDATE pshai.source SET hypocentral_depth=NUll WHERE id=2;
UPDATE pshai.source SET r_depth_distr_id=NULL WHERE id=2;

-- Failure because no magnitude value is set
INSERT INTO eqcat.magnitude(id) VALUES(1023456789);
UPDATE eqcat.magnitude SET mw_val=NULL WHERE id=1;

-- Is the 'last_update' time stamp refreshed on UPDATE?
SELECT gid, last_update FROM pshai.focal_mechanism ORDER BY gid;
UPDATE pshai.focal_mechanism SET gid='focal_mechanism/1/u' WHERE id=1;
SELECT gid, last_update FROM pshai.focal_mechanism ORDER BY gid;
