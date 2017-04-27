Demo Classical PSHA for Vancouver Schools
=========================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7610.hdf5 Wed Apr 26 15:55:36 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 3, sitecol = 917 B

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.1               
area_source_discretization      50.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `nbc_asc_logic_tree.xml <nbc_asc_logic_tree.xml>`_          
job_ini                 `job.ini <job.ini>`_                                        
sites                   `vancouver_school_sites.csv <vancouver_school_sites.csv>`_  
source                  `vancouver_area_source.xml <vancouver_area_source.xml>`_    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ======================================================== =============== ================
smlt_path weight source_model_file                                        gsim_logic_tree num_realizations
========= ====== ======================================================== =============== ================
b1        1.000  `vancouver_area_source.xml <vancouver_area_source.xml>`_ simple(3)       3/3             
========= ====== ======================================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================================================================================== ========= ========== ==========
grp_id gsims                                                                                                                                      distances siteparams ruptparams
====== ========================================================================================================================================== ========= ========== ==========
0      GMPETable(gmpe_table='Wcrust_high_rhypo.hdf5') GMPETable(gmpe_table='Wcrust_low_rhypo.hdf5') GMPETable(gmpe_table='Wcrust_med_rhypo.hdf5') rhypo                mag       
====== ========================================================================================================================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,GMPETable(gmpe_table='Wcrust_high_rhypo.hdf5'): ['<2,b1~b13,w=0.16>']
  0,GMPETable(gmpe_table='Wcrust_low_rhypo.hdf5'): ['<0,b1~b11,w=0.16>']
  0,GMPETable(gmpe_table='Wcrust_med_rhypo.hdf5'): ['<1,b1~b12,w=0.68>']>

Number of ruptures per tectonic region type
-------------------------------------------
========================= ====== ==================== =========== ============ ============
source_model              grp_id trt                  num_sources eff_ruptures tot_ruptures
========================= ====== ==================== =========== ============ ============
vancouver_area_source.xml 0      Active Shallow Crust 1           2430         2,430       
========================= ====== ==================== =========== ============ ============

Informational data
------------------
============================== =================================================================================
count_eff_ruptures.received    tot 2.9 KB, max_per_task 1.45 KB                                                 
count_eff_ruptures.sent        gsims 312.3 KB, sources 19.72 KB, monitor 2.46 KB, srcfilter 1.45 KB, param 130 B
hazard.input_weight            243                                                                              
hazard.n_imts                  3 B                                                                              
hazard.n_levels                36 B                                                                             
hazard.n_realizations          3 B                                                                              
hazard.n_sites                 3 B                                                                              
hazard.n_sources               1 B                                                                              
hazard.output_weight           324                                                                              
hostname                       tstation.gem.lan                                                                 
require_epsilons               0 B                                                                              
============================== =================================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      VICM      AreaSource   2,430        0.0       3         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       1     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.591 0.407  0.303 0.879 2        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         1.182     0.0       2     
reading composite source model   0.022     0.0       1     
store source_info                0.001     0.0       1     
filtering composite source model 9.725E-04 0.0       1     
reading site collection          2.017E-04 0.0       1     
managing sources                 1.323E-04 0.0       1     
saving probability maps          4.792E-05 0.0       1     
aggregate curves                 4.721E-05 0.0       2     
================================ ========= ========= ======