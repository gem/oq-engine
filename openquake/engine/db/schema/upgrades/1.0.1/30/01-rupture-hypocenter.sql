ALTER TABLE hzrdr.probabilistic_rupture DROP COLUMN hypocenter;
ALTER TABLE hzrdr.probabilistic_rupture ADD COLUMN _hypocenter float[3];
