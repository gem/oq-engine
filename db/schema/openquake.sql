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


------------------------------------------------------------------------
-- Table space definitions go here
------------------------------------------------------------------------
CREATE TABLESPACE pshai_ts LOCATION '/var/lib/postgresql/8.4/main/ts/pshai';


------------------------------------------------------------------------
-- Table definitions go here
------------------------------------------------------------------------

-- Fault source
CREATE TABLE pshai.source (
    id SERIAL PRIMARY KEY,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    source_type VARCHAR NOT NULL DEFAULT 'simple'
        CONSTRAINT source_type CHECK
        (source_type IN ('area', 'complex', 'point', 'simple')),
    tectonic_region_id INTEGER NOT NULL,
    rake float NOT NULL
        CONSTRAINT rake_value CHECK ((rake >= -180.0) AND (rake <= 180.0)),
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;


-- Fault rupture
CREATE TABLE pshai.rupture (
    CONSTRAINT pshai_rupture_pk PRIMARY KEY (id),
    magnitude float NOT NULL,
    magnitude_type_id INTEGER NOT NULL
) INHERITS(pshai.source) TABLESPACE pshai_ts;


-- Simple fault geometry
CREATE TABLE pshai.simple_geom (
    id SERIAL PRIMARY KEY,
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
    source_id INTEGER NOT NULL,
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;
SELECT AddGeometryColumn('pshai', 'simple_geom', 'geom', 4326, 'LINESTRING', 2 );


-- Complex fault geometry
CREATE TABLE pshai.complex_geom (
    id SERIAL PRIMARY KEY,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    source_id INTEGER NOT NULL,
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;


-- Fault edge
CREATE TABLE pshai.fault_edge (
    id SERIAL PRIMARY KEY,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    complex_geom_id INTEGER NOT NULL,
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;
SELECT AddGeometryColumn('pshai', 'fault_edge', 'top', 4326, 'LINESTRING', 2 );
SELECT AddGeometryColumn('pshai', 'fault_edge', 'bottom', 4326, 'LINESTRING', 2 );


CREATE TABLE pshai.tectonic_region (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL
) TABLESPACE pshai_ts;


CREATE TABLE pshai.magnitude_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL
) TABLESPACE pshai_ts;


-- Magnitude frequency distribution, base table.
CREATE TABLE pshai.mfd (
    id SERIAL PRIMARY KEY,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    mfd_type VARCHAR(3) NOT NULL,
    magnitude_type_id INTEGER NOT NULL
) TABLESPACE pshai_ts;


-- Magnitude frequency distribution, Evenly discretized
CREATE TABLE pshai.mfd_evd (
    CONSTRAINT pshai_mfd_evd_pk PRIMARY KEY (id),
    CONSTRAINT pshai_mfd_evd_correct_type CHECK(mfd_type = 'evd'),
    min float NOT NULL,
    bin_size float NOT NULL,
    values float[] NOT NULL
) INHERITS(pshai.mfd) TABLESPACE pshai_ts;


-- Magnitude frequency distribution, Truncated Gutenberg Richter
CREATE TABLE pshai.mfd_tgr (
    CONSTRAINT pshai_mfd_tgr_pk PRIMARY KEY (id),
    CONSTRAINT pshai_mfd_tgr_correct_type CHECK(mfd_type = 'tgr'),
    min float NOT NULL,
    max float NOT NULL,
    a_value float NOT NULL,
    b_value float NOT NULL
) INHERITS(pshai.mfd) TABLESPACE pshai_ts;


-- Rupture depth distribution
CREATE TABLE pshai.rdd (
    id SERIAL PRIMARY KEY,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    magnitude float,
    depth float
) TABLESPACE pshai_ts;


CREATE TABLE pshai.strike_dip_rake (
    id SERIAL PRIMARY KEY,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,

    strike float NOT NULL
        CONSTRAINT strike_value CHECK ((strike >= 0.0) AND (strike <= 360.0)),
    dip float NOT NULL
        CONSTRAINT dip_value CHECK ((dip >= 0.0) AND (dip <= 90.0)),
    rake float NOT NULL
        CONSTRAINT rake_value CHECK ((rake >= -180.0) AND (rake <= 180.0)),
    date_created timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;

ALTER TABLE pshai.source ADD CONSTRAINT pshai_source_tectonic_region_fk
FOREIGN KEY (tectonic_region_id) REFERENCES pshai.tectonic_region(id) ON DELETE RESTRICT;

ALTER TABLE pshai.simple_geom ADD CONSTRAINT pshai_simple_geom_source_fk
FOREIGN KEY (source_id) REFERENCES pshai.source(id) ON DELETE CASCADE;

ALTER TABLE pshai.complex_geom ADD CONSTRAINT pshai_complex_geom_source_fk
FOREIGN KEY (source_id) REFERENCES pshai.source(id) ON DELETE CASCADE;

ALTER TABLE pshai.fault_edge ADD CONSTRAINT pshai_fault_edge_complex_geom_fk
FOREIGN KEY (complex_geom_id) REFERENCES pshai.complex_geom(id) ON DELETE CASCADE;

ALTER TABLE pshai.rupture ADD CONSTRAINT pshai_rupture_magnitude_type_fk
FOREIGN KEY (magnitude_type_id) REFERENCES pshai.magnitude_type(id) ON DELETE RESTRICT;

ALTER TABLE pshai.mfd ADD CONSTRAINT pshai_mfd_magnitude_type_fk
FOREIGN KEY (magnitude_type_id) REFERENCES pshai.magnitude_type(id) ON DELETE RESTRICT;
