DROP INDEX hzrdr.hzrdr_ses_rupture_tag_idx;
DROP INDEX hzrdr.hzrdr_ses_rupture_ses_id_idx;
ALTER TABLE riskr.event_loss_data
DROP CONSTRAINT riskr_event_loss_data_sesrupture_fk;

ALTER TABLE hzrdr.ses_rupture RENAME TO probabilistic_rupture;

ALTER TABLE hzrdr.probabilistic_rupture
ADD COLUMN ses_collection_id INTEGER;

ALTER TABLE hzrdr.probabilistic_rupture
ADD CONSTRAINT hzrdr_probabilistic_rupture_ses_collection_fk
FOREIGN KEY (ses_collection_id) REFERENCES hzrdr.ses_collection(id);

GRANT SELECT,INSERT ON hzrdr.probabilistic_rupture TO oq_job_init;

CREATE TABLE hzrdr.ses_rupture (
    id SERIAL PRIMARY KEY,
    ses_id INTEGER NOT NULL,
    rupture_id INTEGER NOT NULL,  -- FK to probabilistic_rupture.id
    tag VARCHAR NOT NULL,
    seed INTEGER NOT NULL
) TABLESPACE hzrdr_ts;

ALTER TABLE hzrdr.ses_rupture OWNER TO oq_admin;

ALTER TABLE hzrdr.ses_rupture
ADD CONSTRAINT hzrdr_ses_rupture_probabilistic_rupture_fk
FOREIGN KEY (rupture_id) REFERENCES hzrdr.probabilistic_rupture(id);

INSERT INTO hzrdr.ses_rupture (ses_id, rupture_id, tag, seed)
SELECT ses_id, id, tag, 0 FROM hzrdr.probabilistic_rupture;

UPDATE hzrdr.probabilistic_rupture
SET ses_collection_id=s.ses_collection_id
FROM hzrdr.ses AS s WHERE ses_id = s.id;

ALTER TABLE hzrdr.probabilistic_rupture
ALTER COLUMN ses_collection_id SET NOT NULL;

ALTER TABLE hzrdr.probabilistic_rupture DROP COLUMN ses_id;

CREATE INDEX hzrdr_ses_rupture_tag_idx ON hzrdr.ses_rupture (tag);
CREATE INDEX hzrdr_ses_rupture_ses_idx ON hzrdr.ses_rupture (ses_id);
ALTER TABLE riskr.event_loss_data
ADD CONSTRAINT riskr_event_loss_data_sesrupture_fk
FOREIGN KEY (rupture_id) REFERENCES hzrdr.ses_rupture(id) ON DELETE CASCADE;
