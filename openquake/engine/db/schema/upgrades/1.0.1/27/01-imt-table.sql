-- this is convenient to have tests changing the risk parameters on the fly
GRANT SELECT,INSERT,UPDATE ON uiapi.risk_calculation TO oq_job_init;

ALTER TABLE hzrdr.probabilistic_rupture DROP COLUMN tectonic_region_type;
ALTER TABLE hzrdr.probabilistic_rupture ADD COLUMN trt_model_id INTEGER;

-- hzrdr.probabilistic_rupture to hzrdr.trt_model FK
ALTER TABLE hzrdr.probabilistic_rupture
ADD CONSTRAINT hzrdr_probabilistic_rupture_trt_model_fk
FOREIGN KEY (trt_model_id) REFERENCES hzrdr.trt_model(id)
ON DELETE CASCADE;

ALTER TABLE hzrdr.trt_model ALTER COLUMN lt_model_id DROP NOT NULL;

CREATE UNIQUE INDEX hzrdr_assoc_lt_rlz_trt_model_uniq_idx ON 
hzrdr.assoc_lt_rlz_trt_model(rlz_id, trt_model_id);

-- imt table ----------------------------------------------------------
/*
NB: the imt_check
CHECK(imt_str = CASE
      WHEN im_type = 'SA' THEN 'SA(' || sa_period::TEXT || ')'
      ELSE im_type END)
was removed on purpose. The reason is that SA(1.0) becomes
SA(1) for postgres and the constraint cannot be satisfied.
I may consider removing all the constraints later on.
*/
CREATE TABLE hzrdi.imt(
  id SERIAL PRIMARY KEY,
  imt_str VARCHAR UNIQUE NOT NULL, -- full string representation of the IMT
  im_type VARCHAR NOT NULL, -- short string for the IMT
  sa_period FLOAT CONSTRAINT imt_sa_period
        CHECK(((im_type = 'SA') AND (sa_period IS NOT NULL))
              OR ((im_type != 'SA') AND (sa_period IS NULL))),
  sa_damping FLOAT CONSTRAINT imt_sa_damping
        CHECK(((im_type = 'SA') AND (sa_damping IS NOT NULL))
            OR ((im_type != 'SA') AND (sa_damping IS NULL))),
  UNIQUE (im_type, sa_period, sa_damping)
) TABLESPACE hzrdi_ts;

ALTER TABLE hzrdi.imt OWNER TO oq_admin;
GRANT SELECT, INSERT ON hzrdi.imt TO oq_job_init;
GRANT USAGE ON hzrdi.imt_id_seq TO oq_job_init;

-- predefined intensity measure types
INSERT INTO hzrdi.imt (imt_str, im_type, sa_period, sa_damping) VALUES
('PGA', 'PGA', NULL, NULL),
('PGV', 'PGV', NULL, NULL),
('PGD', 'PGD', NULL, NULL),
('IA', 'IA', NULL, NULL),
('RSD', 'RSD', NULL, NULL),
('MMI', 'MMI', NULL, NULL),
('SA(0.1)', 'SA', 0.1, 5.0);

-- gmf_rupture table ---------------------------------------------------

CREATE TABLE hzrdr.gmf_rupture (
   id SERIAL PRIMARY KEY,
   rupture_id INTEGER NOT NULL,  -- fk to hzrdr.ses_rupture
   gsim TEXT NOT NULL,
   imt TEXT NOT NULL, -- fk to hzrdi.imt
   ground_motion_field FLOAT[] NOT NULL
) TABLESPACE hzrdr_ts;

ALTER TABLE hzrdr.gmf_rupture OWNER TO oq_admin;
GRANT SELECT, INSERT ON hzrdr.gmf_rupture TO oq_job_init;
GRANT USAGE ON hzrdr.gmf_rupture_id_seq TO oq_job_init;

-- hzrdr.gmf_rupture -> hzrdr.ses_rupture FK
ALTER TABLE hzrdr.gmf_rupture
ADD CONSTRAINT hzrdr_gmf_rupture_ses_rupture_fk
FOREIGN KEY (rupture_id)
REFERENCES hzrdr.ses_rupture(id)
ON DELETE CASCADE;

-- hzrdr.gmf_rupture -> hzrdi.imt FK
ALTER TABLE hzrdr.gmf_rupture
ADD CONSTRAINT hzrdr_gmf_rupture_imt_fk
FOREIGN KEY (imt)
REFERENCES hzrdi.imt(imt_str)
ON DELETE CASCADE;

-- hzrdr.gmf_rupture -> hzrdr.ses_rupture FK
ALTER TABLE hzrdr.gmf_rupture
ADD CONSTRAINT hzrdr_gmf_rupture_fk
FOREIGN KEY (rupture_id)
REFERENCES hzrdr.ses_rupture(id)
ON DELETE CASCADE;

-- drop gmf_data
-- DROP TABLE hzrdr.gmf_data;

-- gmf_view
CREATE OR REPLACE VIEW hzrdr.gmf_view AS
   SELECT d.id as ses_rup_id, d.tag, b.trt_model_id,
   ses_collection_id, ses_id AS ses_ordinal,
   a.gsim, imt, site_indices, ground_motion_field, rlz_id
   FROM hzrdr.assoc_lt_rlz_trt_model AS a,
   hzrdr.probabilistic_rupture AS b,
   hzrdr.gmf_rupture AS c,
   hzrdr.ses_rupture AS d,
   hzrdr.lt_realization AS e
   WHERE c.rupture_id=d.id
   AND d.rupture_id=b.id
   AND a.trt_model_id=b.trt_model_id
   AND c.gsim=a.gsim
   AND a.rlz_id=e.id;

GRANT SELECT ON hzrdr.gmf_view TO oq_job_init;
