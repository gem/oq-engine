/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

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

-- Grant permissions on the recreated view
GRANT SELECT ON pshai.simple_source TO GROUP openquake;
