ALTER TABLE hzrdr.ses_rupture RENAME COLUMN magnitude TO old_magnitude;
ALTER TABLE hzrdr.ses_rupture RENAME COLUMN strike TO old_strike;
ALTER TABLE hzrdr.ses_rupture RENAME COLUMN dip TO old_dip;
ALTER TABLE hzrdr.ses_rupture RENAME COLUMN rake TO old_rake;
ALTER TABLE hzrdr.ses_rupture RENAME COLUMN tectonic_region_type TO old_tectonic_region_type;
ALTER TABLE hzrdr.ses_rupture RENAME COLUMN is_from_fault_source TO old_is_from_fault_source;
ALTER TABLE hzrdr.ses_rupture RENAME COLUMN is_multi_surface TO old_is_multi_surface;
ALTER TABLE hzrdr.ses_rupture RENAME COLUMN lons TO old_lons;
ALTER TABLE hzrdr.ses_rupture RENAME COLUMN lats TO old_lats;
ALTER TABLE hzrdr.ses_rupture RENAME COLUMN depths TO old_depths;
ALTER TABLE hzrdr.ses_rupture RENAME COLUMN surface TO old_surface;


ALTER TABLE hzrdr.ses_rupture ADD COLUMN rupture BYTEA NOT NULL DEFAULT 'not computed';

