-- global simple_fault view, needed for Geonode integration
CREATE VIEW pshai.simple_fault_geo_view AS
SELECT
    pshai.simple_fault.id AS fault_id,
    pshai.simple_fault.owner_id AS fault_owner_id,
    pshai.simple_fault.gid AS fault_gid,
    pshai.simple_fault.name AS fault_name,
    pshai.simple_fault.description, pshai.simple_fault.dip,
    pshai.simple_fault.upper_depth, pshai.simple_fault.lower_depth,
    pshai.simple_fault.last_update AS fault_last_update,
    pshai.simple_fault.edge, pshai.simple_fault.outline,
    pshai.mfd_evd.owner_id AS pshai_mfd_evd_owner_id,
    pshai.mfd_evd.magnitude_type AS pshai_mfd_evd_magnitude_type,
    pshai.mfd_evd.min_val AS pshai_mfd_evd_min_val,
    pshai.mfd_evd.max_val AS pshai_mfd_evd_max_val,
    pshai.mfd_evd.bin_size AS pshai_mfd_evd_bin_size,
    pshai.mfd_evd.mfd_values AS pshai_mfd_evd_pshai_mfd_values,
    pshai.mfd_evd.total_cumulative_rate AS pshai_mfd_evd_total_cumulative_rate,
    pshai.mfd_evd.total_moment_rate AS pshai_mfd_evd_total_moment_rate,
    pshai.mfd_evd.last_update AS pshai_mfd_evd_last_update,
    pshai.mfd_tgr.owner_id AS pshai_mfd_tgr_owner_id,
    pshai.mfd_tgr.magnitude_type AS pshai_mfd_tgr_magnitude_type,
    pshai.mfd_tgr.min_val AS pshai_mfd_tgr_min_val,
    pshai.mfd_tgr.max_val AS pshai_mfd_tgr_max_val,
    pshai.mfd_tgr.a_val AS pshai_mfd_tgr_a_val,
    pshai.mfd_tgr.b_val AS pshai_mfd_tgr_b_val,
    pshai.mfd_tgr.total_cumulative_rate AS pshai_mfd_tgr_total_cumulative_rate,
    pshai.mfd_tgr.total_moment_rate AS pshai_mfd_tgr_total_moment_rate,
    pshai.mfd_tgr.last_update AS pshai_mfd_tgr_last_update
FROM
     pshai.simple_fault
LEFT OUTER JOIN pshai.mfd_evd ON pshai.mfd_evd.id = pshai.simple_fault.mfd_evd_id
LEFT OUTER JOIN pshai.mfd_tgr ON pshai.mfd_tgr.id  = pshai.simple_fault.mfd_tgr_id;

COMMENT ON VIEW pshai.simple_fault_geo_view IS 'A global simple_fault view, needed for geonode integration, it includes mfd_evd and mfd_tgr tables';
