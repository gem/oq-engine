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

-- First drop the views to be merged.
DROP VIEW pshai.simple_source;
DROP VIEW pshai.simple_fault_geo_view;

-- Now add the combined view.
CREATE VIEW pshai.simple_source AS
SELECT
    -- Columns specific to pshai.source
    pshai.source.id,
    pshai.source.owner_id,
    pshai.source.input_id,
    pshai.source.gid,
    pshai.source.name,
    pshai.source.description,
    pshai.source.si_type,
    pshai.source.tectonic_region,
    pshai.source.rake,

    -- Columns specific to pshai.simple_fault
    pshai.simple_fault.dip,
    pshai.simple_fault.upper_depth,
    pshai.simple_fault.lower_depth,
    pshai.simple_fault.edge,
    pshai.simple_fault.outline,

    CASE WHEN mfd_evd_id IS NOT NULL THEN 'evd' ELSE 'tgr' END AS mfd_type,

    -- Common MFD columns, only one of each will be not NULL.
    COALESCE(pshai.mfd_evd.magnitude_type, pshai.mfd_tgr.magnitude_type)
        AS magnitude_type,
    COALESCE(pshai.mfd_evd.min_val, pshai.mfd_tgr.min_val) AS min_val,
    COALESCE(pshai.mfd_evd.max_val, pshai.mfd_tgr.max_val) AS max_val,
    COALESCE(pshai.mfd_evd.total_cumulative_rate,
             pshai.mfd_tgr.total_cumulative_rate) AS total_cumulative_rate,
    COALESCE(pshai.mfd_evd.total_moment_rate,
             pshai.mfd_tgr.total_moment_rate) AS total_moment_rate,

    -- Columns specific to pshai.mfd_evd
    pshai.mfd_evd.bin_size AS evd_bin_size,
    pshai.mfd_evd.mfd_values AS evd_values,

    -- Columns specific to pshai.mfd_tgr
    pshai.mfd_tgr.a_val AS tgr_a_val,
    pshai.mfd_tgr.b_val AS tgr_b_val
FROM
    pshai.source
JOIN pshai.simple_fault ON pshai.simple_fault.id = pshai.source.simple_fault_id
LEFT OUTER JOIN pshai.mfd_evd ON
    pshai.mfd_evd.id = pshai.simple_fault.mfd_evd_id
LEFT OUTER JOIN pshai.mfd_tgr ON
    pshai.mfd_tgr.id  = pshai.simple_fault.mfd_tgr_id;
