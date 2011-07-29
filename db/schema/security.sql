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
GRANT USAGE ON SCHEMA oqmif TO GROUP openquake;
GRANT USAGE ON SCHEMA pshai TO GROUP openquake;
GRANT USAGE ON SCHEMA uiapi TO GROUP openquake;

GRANT ALL ON SEQUENCE admin.oq_user_id_seq TO oq_admin;
GRANT ALL ON SEQUENCE admin.organization_id_seq TO oq_admin;

GRANT ALL ON SEQUENCE eqcat.catalog_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE eqcat.magnitude_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE eqcat.surface_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE oqmif.exposure_model_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE oqmif.exposure_data_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE pshai.complex_fault_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.fault_edge_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.focal_mechanism_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.mfd_evd_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.mfd_tgr_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.r_depth_distr_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.r_rate_mdl_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.rupture_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.simple_fault_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.source_id_seq to GROUP openquake;

GRANT ALL ON SEQUENCE uiapi.loss_curve_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.loss_curve_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.hazard_map_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.hazard_map_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.hazard_curve_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.hazard_curve_node_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.gmf_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.input_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.loss_map_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.loss_map_data_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.oq_job_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.oq_params_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.output_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE uiapi.upload_id_seq to GROUP openquake;

GRANT SELECT ON geography_columns TO GROUP openquake;
GRANT SELECT ON geometry_columns TO GROUP openquake;

GRANT SELECT ON pshai.complex_source TO GROUP openquake;
GRANT SELECT ON pshai.simple_source TO GROUP openquake;
GRANT SELECT ON pshai.complex_rupture TO GROUP openquake;
GRANT SELECT ON pshai.simple_rupture TO GROUP openquake;

-- admin.oq_user
GRANT SELECT ON admin.oq_user TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON admin.oq_user TO oq_admin;

-- admin.organization
GRANT SELECT ON admin.organization TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON admin.organization TO oq_admin;

-- eqcat.catalog
GRANT SELECT ON eqcat.catalog TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON eqcat.catalog TO oq_eqcat_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON eqcat.catalog TO oq_eqcat_writer;

-- eqcat.magnitude
GRANT SELECT ON eqcat.magnitude TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON eqcat.magnitude TO oq_eqcat_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON eqcat.magnitude TO oq_eqcat_writer;

-- eqcat.surface
GRANT SELECT ON eqcat.surface TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON eqcat.surface TO oq_eqcat_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON eqcat.surface TO oq_eqcat_writer;

-- eqcat.catalog_allfields view
GRANT SELECT ON eqcat.catalog_allfields TO GROUP openquake;

-- oqmif.exposure_model
GRANT SELECT ON oqmif.exposure_model TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON oqmif.exposure_model TO oq_ged4gem;

-- oqmif.exposure_data
GRANT SELECT ON oqmif.exposure_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON oqmif.exposure_data TO oq_ged4gem;

-- pshai.complex_fault
GRANT SELECT ON pshai.complex_fault TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.complex_fault TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.complex_fault TO oq_pshai_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.complex_fault TO oq_uiapi_writer;

-- pshai.fault_edge
GRANT SELECT ON pshai.fault_edge TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.fault_edge TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.fault_edge TO oq_pshai_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.fault_edge TO oq_uiapi_writer;

-- pshai.focal_mechanism
GRANT SELECT ON pshai.focal_mechanism TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.focal_mechanism TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.focal_mechanism TO oq_pshai_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.focal_mechanism TO oq_uiapi_writer;

-- pshai.mfd_evd
GRANT SELECT ON pshai.mfd_evd TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.mfd_evd TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.mfd_evd TO oq_pshai_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.mfd_evd TO oq_uiapi_writer;

-- pshai.mfd_tgr
GRANT SELECT ON pshai.mfd_tgr TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.mfd_tgr TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.mfd_tgr TO oq_pshai_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.mfd_tgr TO oq_uiapi_writer;

-- pshai.r_depth_distr
GRANT SELECT ON pshai.r_depth_distr TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.r_depth_distr TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.r_depth_distr TO oq_pshai_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.r_depth_distr TO oq_uiapi_writer;

-- pshai.r_rate_mdl
GRANT SELECT ON pshai.r_rate_mdl TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.r_rate_mdl TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.r_rate_mdl TO oq_pshai_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.r_rate_mdl TO oq_uiapi_writer;

-- pshai.rupture
GRANT SELECT ON pshai.rupture TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.rupture TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.rupture TO oq_pshai_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.rupture TO oq_uiapi_writer;

-- pshai.simple_fault
GRANT SELECT ON pshai.simple_fault TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.simple_fault TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.simple_fault TO oq_pshai_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.simple_fault TO oq_uiapi_writer;

-- pshai.source
GRANT SELECT ON pshai.source TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.source TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.source TO oq_pshai_writer;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.source TO oq_uiapi_writer;

-- uiapi.hazard_map
GRANT SELECT ON uiapi.hazard_map TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.hazard_map TO oq_uiapi_writer;

-- uiapi.hazard_map_data
GRANT SELECT ON uiapi.hazard_map_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.hazard_map_data TO oq_uiapi_writer;

-- uiapi.hazard_curve_data
GRANT SELECT ON uiapi.hazard_curve_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.hazard_curve_data TO oq_uiapi_writer;

-- uiapi.hazard_curve_node_data
GRANT SELECT ON uiapi.hazard_curve_node_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.hazard_curve_node_data TO oq_uiapi_writer;

-- uiapi.gmf_data
GRANT SELECT ON uiapi.gmf_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.gmf_data TO oq_uiapi_writer;

-- uiapi.loss_curve
GRANT SELECT ON uiapi.loss_curve TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.loss_curve TO oq_uiapi_writer;

-- uiapi.loss_curve_data
GRANT SELECT ON uiapi.loss_curve_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.loss_curve_data TO oq_uiapi_writer;

-- uiapi.input
GRANT SELECT ON uiapi.input TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.input TO oq_uiapi_writer;

-- uiapi.loss_map
GRANT SELECT ON uiapi.loss_map TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.loss_map TO oq_uiapi_writer;

-- uiapi.loss_map_data
GRANT SELECT ON uiapi.loss_map_data TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.loss_map_data TO oq_uiapi_writer;

-- uiapi.oq_job
GRANT SELECT ON uiapi.oq_job TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.oq_job TO oq_uiapi_writer;

-- uiapi.oq_params
GRANT SELECT ON uiapi.oq_params TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.oq_params TO oq_uiapi_writer;

-- uiapi.output
GRANT SELECT ON uiapi.output TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.output TO oq_uiapi_writer;

-- uiapi.upload
GRANT SELECT ON uiapi.upload TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.upload TO oq_uiapi_writer;
