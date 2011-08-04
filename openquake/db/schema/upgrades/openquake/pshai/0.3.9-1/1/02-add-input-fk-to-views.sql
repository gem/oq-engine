/*
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
