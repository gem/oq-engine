/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


CREATE INDEX uiapi_input_owner_id_idx on uiapi.input(owner_id);
CREATE INDEX uiapi_oq_job_owner_id_idx on uiapi.oq_job(owner_id);
CREATE INDEX uiapi_output_owner_id_idx on uiapi.output(owner_id);
CREATE INDEX uiapi_upload_owner_id_idx on uiapi.upload(owner_id);

-- uiapi indexes on foreign keys
CREATE INDEX uiapi_hazard_map_data_output_id_idx on uiapi.hazard_map_data(output_id);
CREATE INDEX uiapi_oq_params_upload_id_idx on uiapi.oq_params(upload_id);
CREATE INDEX uiapi_loss_map_data_output_id_idx on uiapi.loss_map_data(output_id);
