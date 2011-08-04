/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- pshai.source and pshai.rupture need to be associated with uiapi.input
-- This patch exposes the needed foreign keys in the simple_source/rupture and
-- complex_source/rupture views.

-- First drop the views in question.
DROP VIEW pshai.simple_source;
DROP VIEW pshai.simple_rupture;
DROP VIEW pshai.complex_source;
DROP VIEW pshai.complex_rupture;

-- Now recreate them all.

-- simple source view, needed for Opengeo server integration
CREATE VIEW pshai.simple_source (
    id, owner_id, input_id, gid, name, description, si_type, tectonic_region,
    rake, simple_fault, fault_outline) AS
SELECT
    src.id, src.owner_id, src.input_id, src.gid, src.name, src.description,
    src.si_type, src.tectonic_region, src.rake, sfault.edge, sfault.outline
FROM
    pshai.source src, pshai.simple_fault sfault
WHERE
    src.si_type = 'simple'
    AND src.simple_fault_id = sfault.id;


-- simple rupture view, needed for Opengeo server integration
CREATE VIEW pshai.simple_rupture (
    id, owner_id, input_id, gid, name, description, si_type, tectonic_region,
    rake, magnitude, magnitude_type, edge, fault_outline) AS
SELECT
    rup.id, rup.owner_id, rup.input_id, rup.gid, rup.name, rup.description,
    rup.si_type, rup.tectonic_region, rup.rake, rup.magnitude,
    rup.magnitude_type, sfault.edge, sfault.outline
FROM
    pshai.rupture rup, pshai.simple_fault sfault
WHERE
    rup.si_type = 'simple'
    AND rup.simple_fault_id = sfault.id;


-- complex source view, needed for Opengeo server integration
CREATE VIEW pshai.complex_source (
    id, owner_id, input_id, gid, name, description, si_type, tectonic_region,
    rake, top_edge, bottom_edge, fault_outline) AS
SELECT
    src.id, src.owner_id, src.input_id, src.gid, src.name, src.description,
    src.si_type, src.tectonic_region, src.rake, fedge.top, fedge.bottom,
    cfault.outline
FROM
    pshai.source src, pshai.complex_fault cfault, pshai.fault_edge fedge
WHERE
    src.si_type = 'complex'
    AND src.complex_fault_id = cfault.id AND cfault.fault_edge_id = fedge.id;


-- complex rupture view, needed for Opengeo server integration
CREATE VIEW pshai.complex_rupture (
    id, owner_id, input_id, gid, name, description, si_type, tectonic_region,
    rake, magnitude, magnitude_type, top_edge, bottom_edge, fault_outline) AS
SELECT
    rup.id, rup.owner_id, rup.input_id, rup.gid, rup.name, rup.description,
    rup.si_type, rup.tectonic_region, rup.rake, rup.magnitude,
    rup.magnitude_type, fedge.top, fedge.bottom, cfault.outline
FROM
    pshai.rupture rup, pshai.complex_fault cfault, pshai.fault_edge fedge
WHERE
    rup.si_type = 'complex'
    AND rup.complex_fault_id = cfault.id AND cfault.fault_edge_id = fedge.id;
