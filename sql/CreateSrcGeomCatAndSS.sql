-- Table: sourcegeometrycatalog

-- DROP TABLE sourcegeometrycatalog;

CREATE TABLE sourcegeometrycatalog
(
  scid serial NOT NULL, -- Source Geometry Catalog Id
  scprivatetag boolean,
  scshortname character(20), -- Source Geometry catalog short name
  scname character varying(50), -- Source geometry Catalog Name
  scdesc character varying(100), -- Source Geometry Description
  sctypecode character(5), -- Either H-Historic, I-Instrumental, S-synthetic, L-for logictree input srcmodel or combination of all
  scareapolygon character varying(5120), -- Describes area of source geometry catalog
  scareamultipolygon character varying(5120), -- added 12 Mar 2010
  scstartdate timestamp without time zone, -- Source Geometry Start Date
  scenddate timestamp without time zone, -- Source Geometry Catalog End Date
  scsources character varying(255), -- Source Geometry Catalog Sources
  scorigformatid integer, -- Source Geometry Catalog Format ID
  scremarks character varying(255), -- Source Geometry Catalog Remarks
  scpgareapolygon geometry,
  scpgareamultipolygon geometry,
  CONSTRAINT sourcegeometrycatalog_pkey PRIMARY KEY (scid),
  CONSTRAINT enforce_dims_scpgareamultipolygon CHECK (st_ndims(scpgareamultipolygon) = 2),
  CONSTRAINT enforce_dims_scpgareapolygon CHECK (st_ndims(scpgareapolygon) = 2),
  CONSTRAINT enforce_geotype_scpgareamultipolygon CHECK (geometrytype(scpgareamultipolygon) = 'MULTIPOLYGON'::text OR scpgareamultipolygon IS NULL),
  CONSTRAINT enforce_geotype_scpgareapolygon CHECK (geometrytype(scpgareapolygon) = 'POLYGON'::text OR scpgareapolygon IS NULL),
  CONSTRAINT enforce_srid_scpgareamultipolygon CHECK (st_srid(scpgareamultipolygon) = 4326),
  CONSTRAINT enforce_srid_scpgareapolygon CHECK (st_srid(scpgareapolygon) = 4326)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE sourcegeometrycatalog OWNER TO postgres;
GRANT ALL ON TABLE sourcegeometrycatalog TO postgres;

COMMENT ON TABLE sourcegeometrycatalog IS 'Catalog of Sources of Geometry, either Seismic Source Zone or Fault information';
COMMENT ON COLUMN sourcegeometrycatalog.scid IS 'Source Geometry Catalog Id';
COMMENT ON COLUMN sourcegeometrycatalog.scshortname IS 'Source Geometry catalog short name';
COMMENT ON COLUMN sourcegeometrycatalog.scname IS 'Source geometry Catalog Name';
COMMENT ON COLUMN sourcegeometrycatalog.scdesc IS 'Source Geometry Description';
COMMENT ON COLUMN sourcegeometrycatalog.sctypecode IS 'Either H-Historic, I-Instrumental, S-synthetic, L-for logictree input srcmodel or combination of all';
COMMENT ON COLUMN sourcegeometrycatalog.scareapolygon IS 'Describes area of source geometry catalog';
COMMENT ON COLUMN sourcegeometrycatalog.scareamultipolygon IS 'added 12 Mar 2010';
COMMENT ON COLUMN sourcegeometrycatalog.scstartdate IS 'Source Geometry Start Date';
COMMENT ON COLUMN sourcegeometrycatalog.scenddate IS 'Source Geometry Catalog End Date';
COMMENT ON COLUMN sourcegeometrycatalog.scsources IS 'Source Geometry Catalog Sources';
COMMENT ON COLUMN sourcegeometrycatalog.scorigformatid IS 'Source Geometry Catalog Format ID';
COMMENT ON COLUMN sourcegeometrycatalog.scremarks IS 'Source Geometry Catalog Remarks';

-- Table: seismicsource

-- DROP TABLE seismicsource;

CREATE TABLE seismicsource
(
  ssid serial NOT NULL, -- Seismic Source Id
  sssrctypecode integer, -- Source Type, 1-fault (usually MULTILINESTRING or multipolygon), 2-Zone (MULTIPOLYGON), 3-Gridded Seis (Point), 4-Seis Point (Point) 5-Subduction zone (top multilinestring, bottom multilinestring)
  ssgeomtypecode integer, -- 1- Point (grid seis or seismic point), M- multilinestring (fault), 3- multipolygon (zone)
  ssgrdefaulttag boolean, -- Gutenberg Richter Default tag, T if default is gutenberg richter, false otherwise
  ssorigid character(50), -- Source Original ID
  ssshortname character(20), -- Source Short Name
  ssname character varying(50), -- Source Name
  ssdesc character varying(100), -- Source Description
  ssremarks character varying(255), -- Source Remarks
  ssarea double precision, -- Source Area, if multipolygon
  ssanormalized double precision, -- Source A normalized
  ssdepth double precision,
  ssmultilinestring character varying(5120), -- Source Fault multilinestring, if fault
  sstopmultilinestring character varying(5120), -- added 12March 2010
  ssbottommultilinestring character varying(5120), -- added 12March 2010
  sspolygon character varying(5120), -- Source Zone Polygon, if source zone
  ssmultipolygon character varying(5120), -- added 12 Mar 2010, in case there are multipolygons
  sspoint character varying(255), -- Seismic Point, if seismic point or gridded seis, in EWKT
  ssbackgrdzonetag boolean, -- Seismic Zone Background tag, if seismic zone
  sserrorcode integer, -- source error code, error encountered during processing of original source catalog
  scid integer NOT NULL, -- Source Geometry Catalog Id
  secode character(10), -- Seismotectonic Environment Id
  sspgpolygon geometry,
  sspgmultipolygon geometry,
  sspgmultilinestring geometry,
  sspgtopmultilinestring geometry,
  sspgbottommultilinestring geometry,
  sspgpoint geometry,
  CONSTRAINT seismicsource_pkey PRIMARY KEY (ssid),
  CONSTRAINT fk_seismicsource_1 FOREIGN KEY (scid)
      REFERENCES sourcegeometrycatalog (scid) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT enforce_dims_sspgbottommultilinestring CHECK (st_ndims(sspgbottommultilinestring) = 2),
  CONSTRAINT enforce_dims_sspgmultilinestring CHECK (st_ndims(sspgmultilinestring) = 2),
  CONSTRAINT enforce_dims_sspgmultipolygon CHECK (st_ndims(sspgmultipolygon) = 2),
  CONSTRAINT enforce_dims_sspgpoint CHECK (st_ndims(sspgpoint) = 2),
  CONSTRAINT enforce_dims_sspgpolygon CHECK (st_ndims(sspgpolygon) = 2),
  CONSTRAINT enforce_dims_sspgtopmultilinestring CHECK (st_ndims(sspgtopmultilinestring) = 2),
  CONSTRAINT enforce_geotype_sspgbottommultilinestring CHECK (geometrytype(sspgbottommultilinestring) = 'MULTILINESTRING'::text OR sspgbottommultilinestring IS NULL),
  CONSTRAINT enforce_geotype_sspgmultilinestring CHECK (geometrytype(sspgmultilinestring) = 'MULTILINESTRING'::text OR sspgmultilinestring IS NULL),
  CONSTRAINT enforce_geotype_sspgmultipolygon CHECK (geometrytype(sspgmultipolygon) = 'MULTIPOLYGON'::text OR sspgmultipolygon IS NULL),
  CONSTRAINT enforce_geotype_sspgpoint CHECK (geometrytype(sspgpoint) = 'POINT'::text OR sspgpoint IS NULL),
  CONSTRAINT enforce_geotype_sspgpolygon CHECK (geometrytype(sspgpolygon) = 'POLYGON'::text OR sspgpolygon IS NULL),
  CONSTRAINT enforce_geotype_sspgtopmultilinestring CHECK (geometrytype(sspgtopmultilinestring) = 'MULTILINESTRING'::text OR sspgtopmultilinestring IS NULL),
  CONSTRAINT enforce_srid_sspgbottommultilinestring CHECK (st_srid(sspgbottommultilinestring) = 4326),
  CONSTRAINT enforce_srid_sspgmultilinestring CHECK (st_srid(sspgmultilinestring) = 4326),
  CONSTRAINT enforce_srid_sspgmultipolygon CHECK (st_srid(sspgmultipolygon) = 4326),
  CONSTRAINT enforce_srid_sspgpoint CHECK (st_srid(sspgpoint) = 4326),
  CONSTRAINT enforce_srid_sspgpolygon CHECK (st_srid(sspgpolygon) = 4326),
  CONSTRAINT enforce_srid_sspgtopmultilinestring CHECK (st_srid(sspgtopmultilinestring) = 4326)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE seismicsource OWNER TO postgres;
GRANT ALL ON TABLE seismicsource TO postgres;

COMMENT ON TABLE seismicsource IS 'Contains Seismic Source Data, Faults, Zones, Gridded Seis, Points';
COMMENT ON COLUMN seismicsource.ssid IS 'Seismic Source Id';
COMMENT ON COLUMN seismicsource.sssrctypecode IS 'Source Type, 1-fault (usually MULTILINESTRING or multipolygon), 2-Zone (MULTIPOLYGON), 3-Gridded Seis (Point), 4-Seis Point (Point) 5-Subduction zone (top multilinestring, bottom multilinestring)';
COMMENT ON COLUMN seismicsource.ssgeomtypecode IS '1- Point (grid seis or seismic point), M- multilinestring (fault), 3- multipolygon (zone)';
COMMENT ON COLUMN seismicsource.ssgrdefaulttag IS 'Gutenberg Richter Default tag, T if default is gutenberg richter, false otherwise';
COMMENT ON COLUMN seismicsource.ssorigid IS 'Source Original ID';
COMMENT ON COLUMN seismicsource.ssshortname IS 'Source Short Name';
COMMENT ON COLUMN seismicsource.ssname IS 'Source Name';
COMMENT ON COLUMN seismicsource.ssdesc IS 'Source Description';
COMMENT ON COLUMN seismicsource.ssremarks IS 'Source Remarks';
COMMENT ON COLUMN seismicsource.ssarea IS 'Source Area, if multipolygon';
COMMENT ON COLUMN seismicsource.ssanormalized IS 'Source A normalized';
COMMENT ON COLUMN seismicsource.ssmultilinestring IS 'Source Fault multilinestring, if fault';
COMMENT ON COLUMN seismicsource.sstopmultilinestring IS 'added 12March 2010';
COMMENT ON COLUMN seismicsource.ssbottommultilinestring IS 'added 12March 2010';
COMMENT ON COLUMN seismicsource.sspolygon IS 'Source Zone Polygon, if source zone';
COMMENT ON COLUMN seismicsource.ssmultipolygon IS 'added 12 Mar 2010, in case there are multipolygons';
COMMENT ON COLUMN seismicsource.sspoint IS 'Seismic Point, if seismic point or gridded seis, in EWKT';
COMMENT ON COLUMN seismicsource.ssbackgrdzonetag IS 'Seismic Zone Background tag, if seismic zone';
COMMENT ON COLUMN seismicsource.sserrorcode IS 'source error code, error encountered during processing of original source catalog';
COMMENT ON COLUMN seismicsource.scid IS 'Source Geometry Catalog Id';
COMMENT ON COLUMN seismicsource.secode IS 'Seismotectonic Environment Id';

/* add geometries 
select AddGeometryColumn('','seismicsource','sspgpolygon',4326,'POLYGON',2);
select AddGeometryColumn('','seismicsource','sspgmultipolygon',4326,'MULTIPOLYGON',2);
select AddGeometryColumn('','seismicsource','sspgmultilinestring',4326,'MULTILINESTRING',2);
select AddGeometryColumn('','seismicsource','sspgtopmultilinestring',4326,'MULTILINESTRING',2);
select AddGeometryColumn('','seismicsource','sspgbottommultilinestring',4326,'MULTILINESTRING',2);
select AddGeometryColumn('','seismicsource','sspgpoint',4326,'POINT',2);


select AddGeometryColumn('','sourcegeometrycatalog','scpgareapolygon',4326,'POLYGON',2);
select AddGeometryColumn('','sourcegeometrycatalog','scpgareamultipolygon',4326,'MULTIPOLYGON',2);
*/