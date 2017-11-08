Demo Classical PSHA for Vancouver Schools
=========================================

============== ===================
checksum32     1,369,868,782      
date           2017-11-08T18:07:14
engine_version 2.8.0-gite3d0f56   
============== ===================

num_sites = 3, num_imts = 3

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
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  simple(3)       3/3             
========= ====== =============== ================

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
  0,GMPETable(gmpe_table='Wcrust_high_rhypo.hdf5'): [2]
  0,GMPETable(gmpe_table='Wcrust_low_rhypo.hdf5'): [0]
  0,GMPETable(gmpe_table='Wcrust_med_rhypo.hdf5'): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
========================= ====== ==================== =========== ============ ============
source_model              grp_id trt                  num_sources eff_ruptures tot_ruptures
========================= ====== ==================== =========== ============ ============
vancouver_area_source.xml 0      Active Shallow Crust 1           2,430        2,430       
========================= ====== ==================== =========== ============ ============

Informational data
------------------
=========================== ====================================================================================
count_eff_ruptures.received tot 3.27 KB, max_per_task 857 B                                                     
count_eff_ruptures.sent     gsims 624.61 KB, sources 11.31 KB, param 3.91 KB, srcfilter 2.89 KB, monitor 1.28 KB
hazard.input_weight         729.0                                                                               
hazard.n_imts               3                                                                                   
hazard.n_levels             36                                                                                  
hazard.n_realizations       3                                                                                   
hazard.n_sites              3                                                                                   
hazard.n_sources            1                                                                                   
hazard.output_weight        108.0                                                                               
hostname                    tstation.gem.lan                                                                    
require_epsilons            False                                                                               
=========================== ====================================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      VICM      AreaSource   2,430        0.003     3         30       
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.003     1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.002 3.713E-04 0.001 0.002 4        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.021     0.0       1     
managing sources               0.018     0.0       1     
total count_eff_ruptures       0.007     0.191     4     
store source_info              0.004     0.0       1     
prefiltering source model      0.001     0.0       1     
reading site collection        1.817E-04 0.0       1     
aggregate curves               1.013E-04 0.0       4     
saving probability maps        2.933E-05 0.0       1     
============================== ========= ========= ======