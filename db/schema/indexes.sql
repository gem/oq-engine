/*
  Indexes for the OpenQuake database.

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License version 3
    only, as published by the Free Software Foundation.

    OpenQuake is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License version 3 for more details
   a copy is included in the LICENSE file that accompanied this code).

    You should have received a copy of the GNU Lesser General Public License
    version 3 along with OpenQuake.  If not, see
    <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.
*/

-- admin.oq_user
CREATE UNIQUE INDEX admin_oq_user_user_name_uniq_idx ON admin.oq_user(user_name);

-- admin.revision_info
CREATE UNIQUE INDEX admin_revision_info_artefact_uniq_idx ON admin.revision_info(artefact);

-- eqcat.catalog
CREATE INDEX eqcat_catalog_agency_idx on eqcat.catalog(agency);
CREATE INDEX eqcat_catalog_time_idx on eqcat.catalog(time);
CREATE INDEX eqcat_catalog_depth_idx on eqcat.catalog(depth);
CREATE INDEX eqcat_catalog_point_idx ON eqcat.catalog USING gist(point);

-- hzrdi.fault_edge
CREATE INDEX hzrdi_fault_edge_bottom_idx ON hzrdi.fault_edge USING gist(bottom);
CREATE INDEX hzrdi_fault_edge_top_idx ON hzrdi.fault_edge USING gist(top);

-- hzrdi.rupture
CREATE INDEX hzrdi_rupture_point_idx ON hzrdi.rupture USING gist(point);

-- hzrdi.simple_fault
CREATE INDEX hzrdi_simple_fault_edge_idx ON hzrdi.simple_fault USING gist(edge);

-- hzrdi.source
CREATE INDEX hzrdi_source_area_idx ON hzrdi.source USING gist(area);
CREATE INDEX hzrdi_source_point_idx ON hzrdi.source USING gist(point);

-- index for the 'owner_id' foreign key
CREATE INDEX eqcat_catalog_owner_id_idx on eqcat.catalog(owner_id);
CREATE INDEX hzrdi_complex_fault_owner_id_idx on hzrdi.complex_fault(owner_id);
CREATE INDEX hzrdi_fault_edge_owner_id_idx on hzrdi.fault_edge(owner_id);
CREATE INDEX hzrdi_focal_mechanism_owner_id_idx on hzrdi.focal_mechanism(owner_id);
CREATE INDEX hzrdi_mfd_evd_owner_id_idx on hzrdi.mfd_evd(owner_id);
CREATE INDEX hzrdi_mfd_tgr_owner_id_idx on hzrdi.mfd_tgr(owner_id);
CREATE INDEX hzrdi_r_depth_distr_owner_id_idx on hzrdi.r_depth_distr(owner_id);
CREATE INDEX hzrdi_r_rate_mdl_owner_id_idx on hzrdi.r_rate_mdl(owner_id);
CREATE INDEX hzrdi_rupture_owner_id_idx on hzrdi.rupture(owner_id);
CREATE INDEX hzrdi_simple_fault_owner_id_idx on hzrdi.simple_fault(owner_id);
CREATE INDEX hzrdi_source_owner_id_idx on hzrdi.source(owner_id);

CREATE INDEX uiapi_input_owner_id_idx on uiapi.input(owner_id);
CREATE INDEX uiapi_oq_job_owner_id_idx on uiapi.oq_job(owner_id);
CREATE INDEX uiapi_output_owner_id_idx on uiapi.output(owner_id);
CREATE INDEX uiapi_upload_owner_id_idx on uiapi.upload(owner_id);

-- uiapi indexes on foreign keys
CREATE INDEX uiapi_hazard_map_data_output_id_idx on uiapi.hazard_map_data(output_id);
CREATE INDEX uiapi_hazard_curve_data_output_id_idx on uiapi.hazard_curve_data(output_id);
CREATE INDEX uiapi_hazard_curve_node_data_hazard_curve_data_id_idx on uiapi.hazard_curve_node_data(hazard_curve_data_id);
CREATE INDEX uiapi_gmf_data_output_id_idx on uiapi.gmf_data(output_id);
CREATE INDEX uiapi_oq_params_upload_id_idx on uiapi.oq_params(upload_id);
CREATE INDEX uiapi_loss_map_output_id_idx on uiapi.loss_map(output_id);
CREATE INDEX uiapi_loss_map_data_loss_map_id_idx on uiapi.loss_map_data(loss_map_id);
CREATE INDEX uiapi_loss_curve_output_id_idx on uiapi.loss_curve(output_id);
CREATE INDEX uiapi_loss_curve_data_loss_curve_id_idx on uiapi.loss_curve_data(loss_curve_id);
