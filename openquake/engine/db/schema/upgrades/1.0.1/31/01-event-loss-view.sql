-- event_loss_view
CREATE VIEW riskr.event_loss_view AS
   SELECT b.tag as rupture_tag, c.id AS rupture_id,
   aggregate_loss, output_id, loss_type FROM
   riskr.event_loss_data AS a, hzrdr.ses_rupture AS b,
   hzrdr.probabilistic_rupture AS c, riskr.event_loss as d
   WHERE a.rupture_id=b.id AND b.rupture_id=c.id AND a.event_loss_id=d.id;
   
ALTER VIEW riskr.event_loss_view OWNER TO oq_admin;
   
-- fix a missing DELETE CASCADE
ALTER TABLE hzrdr.probabilistic_rupture
   DROP CONSTRAINT hzrdr_probabilistic_rupture_ses_collection_fk;
ALTER TABLE hzrdr.probabilistic_rupture
   ADD CONSTRAINT hzrdr_probabilistic_rupture_trt_model_fk
   FOREIGN KEY (trt_model_id) REFERENCES hzrdr.trt_model(id)
   ON DELETE CASCADE;
