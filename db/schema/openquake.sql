/*
  OpenQuake database schema definitions.

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


------------------------------------------------------------------------
-- Name space definitions go here
------------------------------------------------------------------------
CREATE SCHEMA pshai;
CREATE SCHEMA eqcat;
CREATE SCHEMA admin;


------------------------------------------------------------------------
-- Table definitions go here
------------------------------------------------------------------------


-- Organization
CREATE TABLE admin.organization (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    address VARCHAR,
    url VARCHAR,
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE admin_ts;


-- OpenQuake users
CREATE TABLE admin.oq_user (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR NOT NULL,
    full_name VARCHAR NOT NULL,
    organization_id INTEGER NOT NULL,
    -- Whether the data owned by the user is visible to the general public.
    data_is_open boolean NOT NULL DEFAULT TRUE,
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE admin_ts;


-- Earthquake catalog
CREATE TABLE eqcat.catalog (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- This is *not* a foreign key.
    eventid INTEGER NOT NULL,
    agency VARCHAR NOT NULL,
    identifier VARCHAR NOT NULL,
    time timestamp without time zone NOT NULL,
    -- error in seconds
    time_eror INTEGER NOT NULL,
    -- depth in km
    depth float NOT NULL,
    -- error in km
    depth_error float NOT NULL,
    magnitude_id INTEGER NOT NULL,
    surface_id INTEGER NOT NULL,
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE eqcat_ts;
SELECT AddGeometryColumn('eqcat', 'catalog', 'point', 4326, 'POINT', 2);
ALTER TABLE eqcat.catalog ALTER COLUMN point SET NOT NULL;


-- Earthquake event magnitudes
CREATE TABLE eqcat.magnitude (
    id SERIAL PRIMARY KEY,
    mb_val float,
    mb_val_error float,
    ml_val float,
    ml_val_error float,
    ms_val float,
    ms_val_error float,
    mw_val float,
    mw_val_error float,
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE eqcat_ts;


-- Earthquake event surface (an ellipse with an angle)
CREATE TABLE eqcat.surface (
    id SERIAL PRIMARY KEY,
    -- Semi-minor axis: The shortest radius of an ellipse.
    semi_minor float NOT NULL,
    -- Semi-major axis: The longest radius of an ellipse.
    semi_major float NOT NULL,
    strike float NOT NULL,
        CONSTRAINT strike_value CHECK ((strike >= 0.0) AND (strike <= 360.0)),
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE eqcat_ts;


-- rupture
CREATE TABLE pshai.rupture (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    -- seismic input type
    si_type VARCHAR NOT NULL DEFAULT 'simple'
        CONSTRAINT si_type CHECK (si_type IN ('complex', 'point', 'simple')),
    tectonic_region_id INTEGER NOT NULL,
    rake float,
        CONSTRAINT rake_value CHECK (
            rake is NULL OR ((rake >= -180.0) AND (rake <= 180.0))),
    magnitude float NOT NULL,
    magnitude_type_id INTEGER NOT NULL DEFAULT 1,
    simple_fault_id INTEGER,
    complex_fault_id INTEGER,
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;
SELECT AddGeometryColumn('pshai', 'rupture', 'point', 4326, 'POINT', 3);


-- source
CREATE TABLE pshai.source (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    -- seismic input type
    si_type VARCHAR NOT NULL DEFAULT 'simple'
        CONSTRAINT si_type CHECK
        (si_type IN ('area', 'point', 'complex', 'simple')),
    tectonic_region_id INTEGER NOT NULL,
    simple_fault_id INTEGER,
    complex_fault_id INTEGER,
    rake float,
        CONSTRAINT rake_value CHECK (
            rake is NULL OR ((rake >= -180.0) AND (rake <= 180.0))),
    -- hypocentral depth and the rupture depth distribution are only set for
    -- point/area sources
    hypocentral_depth float,
    r_depth_distr_id INTEGER,
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;
SELECT AddGeometryColumn('pshai', 'source', 'point', 4326, 'POINT', 2);
SELECT AddGeometryColumn('pshai', 'source', 'area', 4326, 'POLYGON', 2);


-- Simple fault geometry
CREATE TABLE pshai.simple_fault (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    dip float NOT NULL
        CONSTRAINT dip_value CHECK ((dip >= 0.0) AND (dip <= 90.0)),
    upper_depth float NOT NULL
        CONSTRAINT upper_depth_val CHECK (upper_depth >= 0.0),
    lower_depth float NOT NULL
        CONSTRAINT lower_depth_val CHECK (lower_depth >= 0.0),
    mfd_tgr_id INTEGER,
    mfd_evd_id INTEGER,
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;
SELECT AddGeometryColumn('pshai', 'simple_fault', 'geom', 4326, 'LINESTRING', 3);
ALTER TABLE pshai.simple_fault ALTER COLUMN geom SET NOT NULL;
SELECT AddGeometryColumn('pshai', 'simple_fault', 'outline', 4326, 'POLYGON', 3);


-- Complex fault geometry
CREATE TABLE pshai.complex_fault (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    mfd_tgr_id INTEGER,
    mfd_evd_id INTEGER,
    fault_edge_id INTEGER NOT NULL,
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;
SELECT AddGeometryColumn('pshai', 'complex_fault', 'outline', 4326, 'POLYGON', 3);


-- Fault edge
CREATE TABLE pshai.fault_edge (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;
SELECT AddGeometryColumn('pshai', 'fault_edge', 'top', 4326, 'LINESTRING', 3);
SELECT AddGeometryColumn('pshai', 'fault_edge', 'bottom', 4326, 'LINESTRING', 3);
ALTER TABLE pshai.fault_edge ALTER COLUMN top SET NOT NULL;
ALTER TABLE pshai.fault_edge ALTER COLUMN bottom SET NOT NULL;


-- Magnitude frequency distribution, Evenly discretized
CREATE TABLE pshai.mfd_evd (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    magnitude_type_id INTEGER NOT NULL DEFAULT 1,
    min_val float NOT NULL,
    bin_size float NOT NULL,
    mfd_values float[] NOT NULL,
    total_cumulative_rate float,
    total_moment_rate float
) TABLESPACE pshai_ts;


-- Magnitude frequency distribution, Truncated Gutenberg Richter
CREATE TABLE pshai.mfd_tgr (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    magnitude_type_id INTEGER NOT NULL DEFAULT 1,
    min_val float NOT NULL,
    max_val float NOT NULL,
    a_val float NOT NULL,
    b_val float NOT NULL,
    total_cumulative_rate float,
    total_moment_rate float
) TABLESPACE pshai_ts;


-- Rupture depth distribution
CREATE TABLE pshai.r_depth_distr (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    magnitude_type_id INTEGER NOT NULL DEFAULT 1,
    magnitude float[] NOT NULL,
    depth float[] NOT NULL
) TABLESPACE pshai_ts;


-- Rupture rate model
CREATE TABLE pshai.r_rate_mdl (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    mfd_tgr_id INTEGER,
    mfd_evd_id INTEGER,
    focal_mechanism_id INTEGER NOT NULL,
    -- There can be 1+ rupture rate models associated with a seismic source
    -- that's why the foreign key sits here.
    source_id INTEGER NOT NULL
) TABLESPACE pshai_ts;


CREATE TABLE pshai.focal_mechanism (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    strike float,
        CONSTRAINT strike_value CHECK (
            strike is NULL OR ((strike >= 0.0) AND (strike <= 360.0))),
    dip float,
        CONSTRAINT dip_value CHECK (
            dip is NULL OR ((dip >= 0.0) AND (dip <= 90.0))),
    rake float,
        CONSTRAINT rake_value CHECK (
            rake is NULL OR ((rake >= -180.0) AND (rake <= 180.0))),
    date_created timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;


-- Enumeration of tectonic region types
CREATE TABLE pshai.tectonic_region (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    name VARCHAR NOT NULL
) TABLESPACE pshai_ts;


-- Enumeration of magnitude types
CREATE TABLE pshai.magnitude_type (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    name VARCHAR NOT NULL
) TABLESPACE pshai_ts;


------------------------------------------------------------------------
-- Constraints (foreign keys etc.) go here
------------------------------------------------------------------------
ALTER TABLE admin.oq_user ADD CONSTRAINT admin_oq_user_organization_fk
FOREIGN KEY (organization_id) REFERENCES admin.organization(id) ON DELETE RESTRICT;

ALTER TABLE pshai.rupture ADD CONSTRAINT pshai_rupture_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.source ADD CONSTRAINT pshai_source_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.simple_fault ADD CONSTRAINT pshai_simple_fault_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.complex_fault ADD CONSTRAINT pshai_complex_fault_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.fault_edge ADD CONSTRAINT pshai_fault_edge_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.tectonic_region ADD CONSTRAINT pshai_tectonic_region_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.magnitude_type ADD CONSTRAINT pshai_magnitude_type_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.mfd_evd ADD CONSTRAINT pshai_mfd_evd_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.mfd_tgr ADD CONSTRAINT pshai_mfd_tgr_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.r_depth_distr ADD CONSTRAINT pshai_r_depth_distr_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.focal_mechanism ADD CONSTRAINT pshai_focal_mechanism_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.r_rate_mdl ADD CONSTRAINT pshai_r_rate_mdl_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE pshai.source ADD CONSTRAINT pshai_source_tectonic_region_fk
FOREIGN KEY (tectonic_region_id) REFERENCES pshai.tectonic_region(id) ON DELETE RESTRICT;

ALTER TABLE pshai.complex_fault ADD CONSTRAINT pshai_complex_fault_fault_edge_fk
FOREIGN KEY (fault_edge_id) REFERENCES pshai.fault_edge(id) ON DELETE RESTRICT;

ALTER TABLE pshai.rupture ADD CONSTRAINT pshai_rupture_magnitude_type_fk
FOREIGN KEY (magnitude_type_id) REFERENCES pshai.magnitude_type(id) ON DELETE RESTRICT;

ALTER TABLE pshai.mfd_evd ADD CONSTRAINT pshai_mfd_evd_magnitude_type_fk
FOREIGN KEY (magnitude_type_id) REFERENCES pshai.magnitude_type(id) ON DELETE RESTRICT;

ALTER TABLE pshai.mfd_tgr ADD CONSTRAINT pshai_mfd_tgr_magnitude_type_fk
FOREIGN KEY (magnitude_type_id) REFERENCES pshai.magnitude_type(id) ON DELETE RESTRICT;

ALTER TABLE pshai.r_depth_distr ADD CONSTRAINT pshai_r_depth_distr_magnitude_type_fk
FOREIGN KEY (magnitude_type_id) REFERENCES pshai.magnitude_type(id) ON DELETE RESTRICT;

ALTER TABLE pshai.r_rate_mdl ADD CONSTRAINT pshai_r_rate_mdl_mfd_tgr_fk
FOREIGN KEY (mfd_tgr_id) REFERENCES pshai.mfd_tgr(id) ON DELETE RESTRICT;

ALTER TABLE pshai.r_rate_mdl ADD CONSTRAINT pshai_r_rate_mdl_mfd_evd_fk
FOREIGN KEY (mfd_evd_id) REFERENCES pshai.mfd_evd(id) ON DELETE RESTRICT;

ALTER TABLE pshai.r_rate_mdl ADD CONSTRAINT pshai_r_rate_mdl_focal_mechanism_fk
FOREIGN KEY (focal_mechanism_id) REFERENCES pshai.focal_mechanism(id) ON DELETE RESTRICT;

ALTER TABLE pshai.r_rate_mdl ADD CONSTRAINT pshai_r_rate_mdl_source_fk
FOREIGN KEY (source_id) REFERENCES pshai.source(id) ON DELETE RESTRICT;

ALTER TABLE pshai.simple_fault ADD CONSTRAINT pshai_simple_fault_mfd_tgr_fk
FOREIGN KEY (mfd_tgr_id) REFERENCES pshai.mfd_tgr(id) ON DELETE RESTRICT;

ALTER TABLE pshai.simple_fault ADD CONSTRAINT pshai_simple_fault_mfd_evd_fk
FOREIGN KEY (mfd_evd_id) REFERENCES pshai.mfd_evd(id) ON DELETE RESTRICT;

ALTER TABLE pshai.complex_fault ADD CONSTRAINT pshai_complex_fault_mfd_tgr_fk
FOREIGN KEY (mfd_tgr_id) REFERENCES pshai.mfd_tgr(id) ON DELETE RESTRICT;

ALTER TABLE pshai.complex_fault ADD CONSTRAINT pshai_complex_fault_mfd_evd_fk
FOREIGN KEY (mfd_evd_id) REFERENCES pshai.mfd_evd(id) ON DELETE RESTRICT;

ALTER TABLE pshai.source ADD CONSTRAINT pshai_source_simple_fault_fk
FOREIGN KEY (simple_fault_id) REFERENCES pshai.simple_fault(id) ON DELETE RESTRICT;

ALTER TABLE pshai.source ADD CONSTRAINT pshai_source_complex_fault_fk
FOREIGN KEY (complex_fault_id) REFERENCES pshai.complex_fault(id) ON DELETE RESTRICT;

ALTER TABLE pshai.source ADD CONSTRAINT pshai_source_r_depth_distr_fk
FOREIGN KEY (r_depth_distr_id) REFERENCES pshai.r_depth_distr(id) ON DELETE RESTRICT;

ALTER TABLE pshai.rupture ADD CONSTRAINT pshai_rupture_simple_fault_fk
FOREIGN KEY (simple_fault_id) REFERENCES pshai.simple_fault(id) ON DELETE RESTRICT;

ALTER TABLE pshai.rupture ADD CONSTRAINT pshai_rupture_complex_fault_fk
FOREIGN KEY (complex_fault_id) REFERENCES pshai.complex_fault(id) ON DELETE RESTRICT;

ALTER TABLE pshai.rupture ADD CONSTRAINT pshai_rupture_tectonic_region_fk
FOREIGN KEY (tectonic_region_id) REFERENCES pshai.tectonic_region(id) ON DELETE RESTRICT;

CREATE TRIGGER pshai_rupture_before_insert_update_trig
BEFORE INSERT OR UPDATE ON pshai.rupture
FOR EACH ROW EXECUTE PROCEDURE check_rupture_sources();

CREATE TRIGGER pshai_source_before_insert_update_trig
BEFORE INSERT OR UPDATE ON pshai.source
FOR EACH ROW EXECUTE PROCEDURE check_source_sources();

CREATE TRIGGER pshai_r_rate_mdl_before_insert_update_trig
BEFORE INSERT OR UPDATE ON pshai.r_rate_mdl
FOR EACH ROW EXECUTE PROCEDURE check_only_one_mfd_set();

CREATE TRIGGER pshai_simple_fault_before_insert_update_trig
BEFORE INSERT OR UPDATE ON pshai.simple_fault
FOR EACH ROW EXECUTE PROCEDURE check_only_one_mfd_set();

CREATE TRIGGER pshai_complex_fault_before_insert_update_trig
BEFORE INSERT OR UPDATE ON pshai.complex_fault
FOR EACH ROW EXECUTE PROCEDURE check_only_one_mfd_set();

ALTER TABLE eqcat.catalog ADD CONSTRAINT eqcat_catalog_owner_fk
FOREIGN KEY (owner_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE eqcat.catalog ADD CONSTRAINT eqcat_catalog_magnitude_fk
FOREIGN KEY (magnitude_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

ALTER TABLE eqcat.catalog ADD CONSTRAINT eqcat_catalog_surface_fk
FOREIGN KEY (surface_id) REFERENCES admin.oq_user(id) ON DELETE RESTRICT;

CREATE TRIGGER eqcat_magnitude_before_insert_update_trig
BEFORE INSERT OR UPDATE ON eqcat.magnitude
FOR EACH ROW EXECUTE PROCEDURE check_magnitude_data();
