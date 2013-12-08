/*
  Copyright (c) 2010-2013, GEM Foundation.

  OpenQuake is free software: you can redistribute it and/or modify it
  under the terms of the GNU Affero General Public License as published
  by the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  OpenQuake is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU Affero General Public License
  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
*/


-- Please note that all OpenQuake database roles are a member of the
-- 'openquake' database group.
-- Granting certain privileges to the 'openquake' group hence applies to all
-- of our database users/roles.

GRANT USAGE ON SCHEMA admin TO GROUP openquake;
GRANT USAGE ON SCHEMA hzrdi TO GROUP openquake;
GRANT USAGE ON SCHEMA hzrdr TO GROUP openquake;
GRANT USAGE ON SCHEMA riski TO GROUP openquake;
GRANT USAGE ON SCHEMA riskr TO GROUP openquake;
GRANT USAGE ON SCHEMA uiapi TO GROUP openquake;

GRANT ALL ON ALL SEQUENCES IN SCHEMA admin TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA hzrdi TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA hzrdr TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA riski TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA riskr TO GROUP openquake;
GRANT ALL ON ALL SEQUENCES IN SCHEMA uiapi TO GROUP openquake;

-- Users in the `openquake` group have read access to everything
GRANT SELECT ON ALL TABLES IN SCHEMA admin TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA hzrdi TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA hzrdr TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA riski TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA riskr TO GROUP openquake;
GRANT SELECT ON ALL TABLES IN SCHEMA uiapi TO GROUP openquake;
GRANT SELECT ON geography_columns          TO GROUP openquake;
GRANT SELECT ON geometry_columns           TO GROUP openquake;
GRANT SELECT ON spatial_ref_sys            TO GROUP openquake;

-- `oq_admin` has full SELECT/INSERT/UPDATE/DELETE access to all tables.
-- In fact, `oq_admin` is the only user that can delete records
-- with the exception the uiapi.performance table.
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA admin TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA hzrdi TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA hzrdr TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA riski TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA riskr TO oq_admin;
GRANT INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA uiapi TO oq_admin;

GRANT ALL ON SCHEMA admin TO oq_admin;
GRANT ALL ON SCHEMA hzrdi TO oq_admin;
GRANT ALL ON SCHEMA hzrdr TO oq_admin;
GRANT ALL ON SCHEMA riski TO oq_admin;
GRANT ALL ON SCHEMA riskr TO oq_admin;
GRANT ALL ON SCHEMA uiapi TO oq_admin;

----------------------------------------------
-- Specific permissions for individual tables:
----------------------------------------------

-- hzrdi schema
GRANT SELECT,INSERT ON hzrdi.hazard_site            TO oq_job_init;
GRANT SELECT,INSERT ON hzrdi.site_model           TO oq_job_init;

-- hzrdr schema
GRANT SELECT,INSERT        ON hzrdr.hazard_curve      TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON hzrdr.hazard_curve_data TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.gmf               TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.gmf_data          TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.disagg_result     TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON hzrdr.hazard_map        TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.uhs               TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.uhs_data          TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON hzrdr.lt_realization    TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.ses_collection    TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.ses               TO oq_job_init;
GRANT SELECT,INSERT        ON hzrdr.ses_rupture       TO oq_job_init;

-- riski schema
GRANT SELECT,INSERT ON ALL TABLES IN SCHEMA riski   TO oq_job_init;
GRANT UPDATE        ON riski.occupancy              TO oq_job_init;

-- riskr schema
GRANT SELECT,INSERT,UPDATE ON riskr.loss_curve                TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_curve_data           TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.aggregate_loss_curve_data TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_map                  TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_map_data             TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_fraction             TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.loss_fraction_data        TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.aggregate_loss            TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.bcr_distribution          TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.bcr_distribution_data     TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.dmg_state                 TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.dmg_dist_per_asset        TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.dmg_dist_per_taxonomy     TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.dmg_dist_total            TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.event_loss                TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON riskr.event_loss_data           TO oq_job_init;

-- uiapi schema
GRANT SELECT,INSERT,UPDATE ON uiapi.oq_job             TO oq_job_init;
-- oq_job_init is granted write access to record job start time and other job stats at job init time
GRANT SELECT,INSERT,UPDATE ON uiapi.job_stats          TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON uiapi.job_stats          TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON uiapi.hazard_calculation TO oq_job_init;
GRANT SELECT,INSERT        ON uiapi.risk_calculation   TO oq_job_init;
-- what nodes became available/unavailable at what time?
GRANT SELECT,INSERT,UPDATE ON uiapi.cnode_stats        TO oq_job_init;
GRANT SELECT,INSERT,UPDATE ON uiapi.output             TO oq_job_init;
GRANT SELECT,INSERT,DELETE ON uiapi.performance        TO oq_job_init;
