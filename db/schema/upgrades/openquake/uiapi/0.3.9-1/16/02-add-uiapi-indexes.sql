/*
    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License version 3
    only, as published by the Free Software Foundation.

    OpenQuake is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License version 3 for more details
    (a copy is included in the LICENSE file that accompanied this code).

    You should have received a copy of the GNU Lesser General Public License
    version 3 along with OpenQuake.  If not, see
    <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.
*/


CREATE INDEX uiapi_input_owner_id_idx on uiapi.input(owner_id);
CREATE INDEX uiapi_oq_job_owner_id_idx on uiapi.oq_job(owner_id);
CREATE INDEX uiapi_output_owner_id_idx on uiapi.output(owner_id);
CREATE INDEX uiapi_upload_owner_id_idx on uiapi.upload(owner_id);

-- uiapi indexes on foreign keys
CREATE INDEX uiapi_hazard_map_data_output_id_idx on uiapi.hazard_map_data(output_id);
CREATE INDEX uiapi_oq_params_upload_id_idx on uiapi.oq_params(upload_id);
CREATE INDEX uiapi_loss_map_data_output_id_idx on uiapi.loss_map_data(output_id);
