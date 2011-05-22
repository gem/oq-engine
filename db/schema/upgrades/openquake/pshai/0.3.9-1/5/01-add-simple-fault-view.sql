-- global simple_fault view, needed for Geonode integration
CREATE VIEW pshai.simple_fault_geo_view AS
SELECT
    pshai.simple_fault.id,
    pshai.simple_fault.gid,
    pshai.simple_fault.name,
    pshai.simple_fault.description,
    pshai.simple_fault.dip,
    pshai.simple_fault.upper_depth,
    pshai.simple_fault.lower_depth,
    pshai.simple_fault.edge,
    pshai.simple_fault.outline,
    CASE WHEN mfd_evd_id IS NOT NULL THEN 'evd' ELSE 'tgr' END AS mfd_type,
    -- Common columns, only one of each will be not NULL.
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
     pshai.simple_fault
LEFT OUTER JOIN pshai.mfd_evd ON pshai.mfd_evd.id = pshai.simple_fault.mfd_evd_id
LEFT OUTER JOIN pshai.mfd_tgr ON pshai.mfd_tgr.id  = pshai.simple_fault.mfd_tgr_id;


COMMENT ON VIEW pshai.simple_fault_geo_view IS 'A simple_fault view, needed for geonode integration, it includes mfd_evd and mfd_tgr tables';
