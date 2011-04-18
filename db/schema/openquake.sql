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


------------------------------------------------------------------------
-- Table definitions go here
------------------------------------------------------------------------


-- rupture
CREATE TABLE pshai.rupture (
    id SERIAL PRIMARY KEY,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    rupture_type VARCHAR NOT NULL DEFAULT 'simple'
        CONSTRAINT rupture_type CHECK
        (rupture_type IN ('complex', 'point', 'simple')),
    tectonic_region_id INTEGER NOT NULL,
    rake float NOT NULL
        CONSTRAINT rake_value CHECK ((rake >= -180.0) AND (rake <= 180.0)),
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL,
    magnitude float NOT NULL,
    magnitude_type_id INTEGER NOT NULL
) TABLESPACE pshai_ts;


-- source
CREATE TABLE pshai.source (
    id SERIAL PRIMARY KEY,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    source_type VARCHAR NOT NULL DEFAULT 'simple'
        CONSTRAINT source_type CHECK
        (source_type IN ('area', 'point', 'complex', 'simple')),
    tectonic_region_id INTEGER NOT NULL,
    rake float NOT NULL
        CONSTRAINT rake_value CHECK ((rake >= -180.0) AND (rake <= 180.0)),
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;


-- Simple fault geometry
CREATE TABLE pshai.simple_fault (
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
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;
SELECT AddGeometryColumn('pshai', 'simple_fault', 'geom', 4326, 'LINESTRING', 2 );
ALTER TABLE pshai.simple_fault ALTER COLUMN geom SET NOT NULL;


-- Complex fault geometry
CREATE TABLE pshai.complex_fault (
    id SERIAL PRIMARY KEY,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
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
    complex_fault_id INTEGER NOT NULL,
    date_created timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE pshai_ts;
SELECT AddGeometryColumn('pshai', 'fault_edge', 'top', 4326, 'LINESTRING', 2 );
SELECT AddGeometryColumn('pshai', 'fault_edge', 'bottom', 4326, 'LINESTRING', 2 );
ALTER TABLE pshai.fault_edge ALTER COLUMN top SET NOT NULL;
ALTER TABLE pshai.fault_edge ALTER COLUMN bottom SET NOT NULL;


-- Enumeration of tectonic region types
CREATE TABLE pshai.tectonic_region (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL
) TABLESPACE pshai_ts;


-- Enumeration of magnitude types
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
    min_val float NOT NULL,
    bin_size float NOT NULL,
    mfd_values float[] NOT NULL
) INHERITS(pshai.mfd) TABLESPACE pshai_ts;


-- Magnitude frequency distribution, Truncated Gutenberg Richter
CREATE TABLE pshai.mfd_tgr (
    CONSTRAINT pshai_mfd_tgr_pk PRIMARY KEY (id),
    CONSTRAINT pshai_mfd_tgr_correct_type CHECK(mfd_type = 'tgr'),
    min_val float NOT NULL,
    max_val float NOT NULL,
    a_val float NOT NULL,
    b_val float NOT NULL
) INHERITS(pshai.mfd) TABLESPACE pshai_ts;


-- Rupture depth distribution
CREATE TABLE pshai.rdd (
    id SERIAL PRIMARY KEY,
    -- gml:id
    gid VARCHAR NOT NULL,
    name VARCHAR,
    description VARCHAR,
    magnitude_type_id INTEGER NOT NULL,
    magnitude float[] NOT NULL,
    depth float[] NOT NULL
) TABLESPACE pshai_ts;


CREATE TABLE pshai.focal_mechanism (
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


-- Link sources and simple geometries
CREATE TABLE pshai.source_to_simple_fault (
    source_id INTEGER NOT NULL,
    geom_id INTEGER NOT NULL
) TABLESPACE pshai_ts;


-- Link sources and complex geometries
CREATE TABLE pshai.source_to_complex_fault (
    source_id INTEGER NOT NULL,
    geom_id INTEGER NOT NULL
) TABLESPACE pshai_ts;


-- Link ruptures and simple geometries
CREATE TABLE pshai.rupture_to_simple_fault (
    rupture_id INTEGER NOT NULL,
    geom_id INTEGER NOT NULL
) TABLESPACE pshai_ts;


-- Link ruptures and complex geometries
CREATE TABLE pshai.rupture_to_complex_fault (
    rupture_id INTEGER NOT NULL,
    geom_id INTEGER NOT NULL
) TABLESPACE pshai_ts;


------------------------------------------------------------------------
-- Constraints (foreign keys etc.) go here
------------------------------------------------------------------------
ALTER TABLE pshai.source ADD CONSTRAINT pshai_source_tectonic_region_fk
FOREIGN KEY (tectonic_region_id) REFERENCES pshai.tectonic_region(id) ON DELETE RESTRICT;

ALTER TABLE pshai.fault_edge ADD CONSTRAINT pshai_fault_edge_complex_fault_fk
FOREIGN KEY (complex_fault_id) REFERENCES pshai.complex_fault(id) ON DELETE CASCADE;

ALTER TABLE pshai.rupture ADD CONSTRAINT pshai_rupture_magnitude_type_fk
FOREIGN KEY (magnitude_type_id) REFERENCES pshai.magnitude_type(id) ON DELETE RESTRICT;

ALTER TABLE pshai.mfd ADD CONSTRAINT pshai_mfd_magnitude_type_fk
FOREIGN KEY (magnitude_type_id) REFERENCES pshai.magnitude_type(id) ON DELETE RESTRICT;

ALTER TABLE pshai.rdd ADD CONSTRAINT pshai_rdd_magnitude_type_fk
FOREIGN KEY (magnitude_type_id) REFERENCES pshai.magnitude_type(id) ON DELETE RESTRICT;

ALTER TABLE pshai.rupture_to_simple_fault ADD CONSTRAINT pshai_rupture_to_simple_fault_rupture_fk
FOREIGN KEY (rupture_id) REFERENCES pshai.rupture(id) ON DELETE CASCADE;
ALTER TABLE pshai.rupture_to_simple_fault ADD CONSTRAINT pshai_rupture_to_simple_fault_geom_fk
FOREIGN KEY (geom_id) REFERENCES pshai.simple_fault(id) ON DELETE CASCADE;

ALTER TABLE pshai.rupture_to_complex_fault ADD CONSTRAINT pshai_rupture_to_complex_fault_rupture_fk
FOREIGN KEY (rupture_id) REFERENCES pshai.rupture(id) ON DELETE CASCADE;
ALTER TABLE pshai.rupture_to_complex_fault ADD CONSTRAINT pshai_rupture_to_complex_fault_geom_fk
FOREIGN KEY (geom_id) REFERENCES pshai.complex_fault(id) ON DELETE CASCADE;

ALTER TABLE pshai.source_to_simple_fault ADD CONSTRAINT pshai_source_to_simple_fault_source_fk
FOREIGN KEY (source_id) REFERENCES pshai.source(id) ON DELETE CASCADE;
ALTER TABLE pshai.source_to_simple_fault ADD CONSTRAINT pshai_source_to_simple_fault_geom_fk
FOREIGN KEY (geom_id) REFERENCES pshai.simple_fault(id) ON DELETE CASCADE;

ALTER TABLE pshai.source_to_complex_fault ADD CONSTRAINT pshai_source_to_complex_fault_source_fk
FOREIGN KEY (source_id) REFERENCES pshai.source(id) ON DELETE CASCADE;
ALTER TABLE pshai.source_to_complex_fault ADD CONSTRAINT pshai_source_to_complex_fault_geom_fk
FOREIGN KEY (geom_id) REFERENCES pshai.complex_fault(id) ON DELETE CASCADE;
