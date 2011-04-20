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


GRANT USAGE ON SCHEMA admin TO GROUP openquake;
GRANT USAGE ON SCHEMA pshai TO GROUP openquake;
GRANT USAGE ON SCHEMA eqcat TO GROUP openquake;

GRANT ALL ON SEQUENCE admin.oq_user_id_seq TO oq_admin;
GRANT ALL ON SEQUENCE admin.organization_id_seq TO oq_admin;

GRANT ALL ON SEQUENCE pshai.complex_fault_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.fault_edge_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.focal_mechanism_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.magnitude_type_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.mfd_evd_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.mfd_tgr_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.r_depth_distr_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.r_rate_mdl_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.rupture_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.simple_fault_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.source_id_seq to GROUP openquake;
GRANT ALL ON SEQUENCE pshai.tectonic_region_id_seq to GROUP openquake;

-- admin.oq_user
GRANT SELECT ON admin.oq_user TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON admin.oq_user TO oq_admin;

-- admin.organization
GRANT SELECT ON admin.organization TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON admin.organization TO oq_admin;

-- pshai.complex_fault
GRANT SELECT ON pshai.complex_fault TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.complex_fault TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.complex_fault TO oq_pshai_writer;

-- pshai.fault_edge
GRANT SELECT ON pshai.fault_edge TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.fault_edge TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.fault_edge TO oq_pshai_writer;

-- pshai.focal_mechanism
GRANT SELECT ON pshai.focal_mechanism TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.focal_mechanism TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.focal_mechanism TO oq_pshai_writer;

-- pshai.magnitude_type
GRANT SELECT ON pshai.magnitude_type TO GROUP openquake;

-- pshai.mfd_evd
GRANT SELECT ON pshai.mfd_evd TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.mfd_evd TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.mfd_evd TO oq_pshai_writer;

-- pshai.mfd_tgr
GRANT SELECT ON pshai.mfd_tgr TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.mfd_tgr TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.mfd_tgr TO oq_pshai_writer;

-- pshai.r_depth_distr
GRANT SELECT ON pshai.r_depth_distr TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.r_depth_distr TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.r_depth_distr TO oq_pshai_writer;

-- pshai.r_rate_mdl
GRANT SELECT ON pshai.r_rate_mdl TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.r_rate_mdl TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.r_rate_mdl TO oq_pshai_writer;

-- pshai.rupture
GRANT SELECT ON pshai.rupture TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.rupture TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.rupture TO oq_pshai_writer;

-- pshai.simple_fault
GRANT SELECT ON pshai.simple_fault TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.simple_fault TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.simple_fault TO oq_pshai_writer;

-- pshai.source
GRANT SELECT ON pshai.source TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE ON pshai.source TO oq_pshai_etl;
GRANT SELECT,INSERT,UPDATE,DELETE ON pshai.source TO oq_pshai_writer;

-- pshai.tectonic_region
GRANT SELECT ON pshai.tectonic_region TO GROUP openquake;
