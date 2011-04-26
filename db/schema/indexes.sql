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

-- pshai.fault_edge
CREATE INDEX pshai_fault_edge_bottom_idx ON pshai.fault_edge USING gist(bottom);
CREATE INDEX pshai_fault_edge_top_idx ON pshai.fault_edge USING gist(top);

-- pshai.rupture
CREATE INDEX pshai_rupture_point_idx ON pshai.rupture USING gist(point);

-- pshai.simple_fault
CREATE INDEX pshai_simple_fault_edge_idx ON pshai.simple_fault USING gist(edge);

-- pshai.source
CREATE INDEX pshai_source_area_idx ON pshai.source USING gist(area);
CREATE INDEX pshai_source_point_idx ON pshai.source USING gist(point);

-- index for the 'owner_id' foreign key
CREATE INDEX eqcat_catalog_owner_id_idx on eqcat.catalog(owner_id);
CREATE INDEX pshai_complex_fault_owner_id_idx on pshai.complex_fault(owner_id);
CREATE INDEX pshai_fault_edge_owner_id_idx on pshai.fault_edge(owner_id);
CREATE INDEX pshai_focal_mechanism_owner_id_idx on pshai.focal_mechanism(owner_id);
CREATE INDEX pshai_mfd_evd_owner_id_idx on pshai.mfd_evd(owner_id);
CREATE INDEX pshai_mfd_tgr_owner_id_idx on pshai.mfd_tgr(owner_id);
CREATE INDEX pshai_r_depth_distr_owner_id_idx on pshai.r_depth_distr(owner_id);
CREATE INDEX pshai_r_rate_mdl_owner_id_idx on pshai.r_rate_mdl(owner_id);
CREATE INDEX pshai_rupture_owner_id_idx on pshai.rupture(owner_id);
CREATE INDEX pshai_simple_fault_owner_id_idx on pshai.simple_fault(owner_id);
CREATE INDEX pshai_source_owner_id_idx on pshai.source(owner_id);
