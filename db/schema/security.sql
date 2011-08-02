/*
  Roles and permissions for the OpenQuake database.

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


-- Please note that all OpenQuake database roles are a member of the
-- 'openquake' database group.
-- Granting certain privileges to the 'openquake' group hence applies to all
-- of our database users/roles.

GRANT USAGE ON SCHEMA admin TO GROUP openquake;
GRANT USAGE ON SCHEMA eqcat TO GROUP openquake;
GRANT USAGE ON SCHEMA hzrdi TO GROUP openquake;
GRANT USAGE ON SCHEMA hzrdo TO GROUP openquake;
GRANT USAGE ON SCHEMA oqmif TO GROUP openquake;
GRANT USAGE ON SCHEMA riski TO GROUP openquake;
GRANT USAGE ON SCHEMA risko TO GROUP openquake;
GRANT USAGE ON SCHEMA uiapi TO GROUP openquake;

GRANT ALL ON SEQUENCE admin.oq_user_id_seq TO oq_admin;
GRANT ALL ON SEQUENCE admin.organization_id_seq TO oq_admin;

GRANT ALL ON SEQUENCE eqcat.catalog_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE eqcat.magnitude_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE eqcat.surface_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE oqmif.exposure_model_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE oqmif.exposure_data_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE hzrdi.complex_fault_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.fault_edge_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.focal_mechanism_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.mfd_evd_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.mfd_tgr_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.r_depth_distr_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.r_rate_mdl_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.rupture_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.simple_fault_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdi.source_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE risko.loss_curve_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE risko.loss_curve_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdo.hazard_map_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdo.hazard_map_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdo.hazard_curve_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdo.hazard_curve_node_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE hzrdo.gmf_data_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE uiapi.input_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE risko.loss_map_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE risko.loss_map_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.oq_job_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.oq_params_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.output_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.upload_id_seq to GROUP openquake;

GRANT SELECT ON geography_columns TO GROUP openquake;
GRANT SELECT ON geometry_columns TO GROUP openquake;

GRANT SELECT ON hzrdi.complex_source TO GROUP openquake;
GRANT SELECT ON hzrdi.simple_source TO GROUP openquake;
GRANT SELECT ON hzrdi.complex_rupture TO GROUP openquake;
GRANT SELECT ON hzrdi.simple_rupture TO GROUP openquake;

-- admin.oq_user
GRANT SELECT ON admin.oq_user TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON admin.oq_user TO oq_admin;

-- admin.organization
GRANT SELECT ON admin.organization TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON admin.organization TO oq_admin;

-- eqcat.catalog
GRANT SELECT ON eqcat.catalog TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON eqcat.catalog TO oq_eqcat_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON eqcat.catalog TO oq_eqcat_writer;

-- eqcat.magnitude
GRANT SELECT ON eqcat.magnitude TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON eqcat.magnitude TO oq_eqcat_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON eqcat.magnitude TO oq_eqcat_writer;

-- eqcat.surface
GRANT SELECT ON eqcat.surface TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON eqcat.surface TO oq_eqcat_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON eqcat.surface TO oq_eqcat_writer;

-- eqcat.catalog_allfields view
GRANT SELECT ON eqcat.catalog_allfields TO GROUP openquake;

-- oqmif.exposure_model
GRANT SELECT ON oqmif.exposure_model TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON oqmif.exposure_model TO oq_ged4gem;

-- oqmif.exposure_data
GRANT SELECT ON oqmif.exposure_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON oqmif.exposure_data TO oq_ged4gem;

-- hzrdi.complex_fault
GRANT SELECT ON hzrdi.complex_fault TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON hzrdi.complex_fault TO oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.complex_fault TO oq_hzrdi_writer;

-- hzrdi.fault_edge
GRANT SELECT ON hzrdi.fault_edge TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON hzrdi.fault_edge TO oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.fault_edge TO oq_hzrdi_writer;

-- hzrdi.focal_mechanism
GRANT SELECT ON hzrdi.focal_mechanism TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON hzrdi.focal_mechanism TO oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.focal_mechanism TO oq_hzrdi_writer;

-- hzrdi.mfd_evd
GRANT SELECT ON hzrdi.mfd_evd TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON hzrdi.mfd_evd TO oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.mfd_evd TO oq_hzrdi_writer;

-- hzrdi.mfd_tgr
GRANT SELECT ON hzrdi.mfd_tgr TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON hzrdi.mfd_tgr TO oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.mfd_tgr TO oq_hzrdi_writer;

-- hzrdi.r_depth_distr
GRANT SELECT ON hzrdi.r_depth_distr TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON hzrdi.r_depth_distr TO oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.r_depth_distr TO oq_hzrdi_writer;

-- hzrdi.r_rate_mdl
GRANT SELECT ON hzrdi.r_rate_mdl TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON hzrdi.r_rate_mdl TO oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.r_rate_mdl TO oq_hzrdi_writer;

-- hzrdi.rupture
GRANT SELECT ON hzrdi.rupture TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON hzrdi.rupture TO oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.rupture TO oq_hzrdi_writer;

-- hzrdi.simple_fault
GRANT SELECT ON hzrdi.simple_fault TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON hzrdi.simple_fault TO oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.simple_fault TO oq_hzrdi_writer;

-- hzrdi.source
GRANT SELECT ON hzrdi.source TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON hzrdi.source TO oq_hzrdi_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdi.source TO oq_hzrdi_writer;

-- hzrdo.hazard_map
GRANT SELECT ON hzrdo.hazard_map TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdo.hazard_map TO oq_reslt_writer;

-- hzrdo.hazard_map_data
GRANT SELECT ON hzrdo.hazard_map_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdo.hazard_map_data TO oq_reslt_writer;

-- hzrdo.hazard_curve_data
GRANT SELECT ON hzrdo.hazard_curve_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdo.hazard_curve_data TO oq_reslt_writer;

-- hzrdo.hazard_curve_node_data
GRANT SELECT ON hzrdo.hazard_curve_node_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdo.hazard_curve_node_data TO oq_reslt_writer;

-- hzrdo.gmf_data
GRANT SELECT ON hzrdo.gmf_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON hzrdo.gmf_data TO oq_reslt_writer;

-- risko.loss_curve
GRANT SELECT ON risko.loss_curve TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON risko.loss_curve TO oq_reslt_writer;

-- risko.loss_curve_data
GRANT SELECT ON risko.loss_curve_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON risko.loss_curve_data TO oq_reslt_writer;

-- uiapi.input
GRANT SELECT ON uiapi.input TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.input TO oq_uiapi_writer;

-- risko.loss_map
GRANT SELECT ON risko.loss_map TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON risko.loss_map TO oq_reslt_writer;

-- risko.loss_map_data
GRANT SELECT ON risko.loss_map_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON risko.loss_map_data TO oq_reslt_writer;

-- uiapi.oq_job
GRANT SELECT ON uiapi.oq_job TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.oq_job TO oq_uiapi_writer;
GRANT SELECT,INSERT,UPDATE ON uiapi.oq_job TO oq_reslt_writer;

-- uiapi.oq_params
GRANT SELECT ON uiapi.oq_params TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.oq_params TO oq_uiapi_writer;
GRANT SELECT,INSERT,UPDATE ON uiapi.oq_params TO oq_reslt_writer;

-- uiapi.output
GRANT SELECT ON uiapi.output TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.output TO oq_uiapi_writer;
GRANT SELECT,INSERT,UPDATE ON uiapi.output TO oq_reslt_writer;

-- uiapi.upload
GRANT SELECT ON uiapi.upload TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.upload TO oq_uiapi_writer;
