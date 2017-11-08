QA test for disaggregation case_2
=================================

============== ===================
checksum32     1,100,395,680      
date           2017-11-08T18:08:05
engine_version 2.8.0-gite3d0f56   
============== ===================

num_sites = 2, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'disaggregation'  
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============== ====== =============== ================
smlt_path      weight gsim_logic_tree num_realizations
============== ====== =============== ================
source_model_1 0.500  simple(1,2)     2/2             
source_model_2 0.500  simple(1,2)     2/2             
============== ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      YoungsEtAl1997SSlab()                 rrup        vs30                    hypo_depth mag   
1      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=4)
  0,YoungsEtAl1997SSlab(): [0 1]
  1,BooreAtkinson2008(): [0]
  1,ChiouYoungs2008(): [1]
  2,BooreAtkinson2008(): [2]
  2,ChiouYoungs2008(): [3]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ============
source_model       grp_id trt                  num_sources eff_ruptures tot_ruptures
================== ====== ==================== =========== ============ ============
source_model_1.xml 0      Subduction Intraslab 1           1,815        1,815       
source_model_1.xml 1      Active Shallow Crust 2           3,630        3,630       
source_model_2.xml 2      Active Shallow Crust 1           1,420        1,420       
================== ====== ==================== =========== ============ ============

============= =====
#TRT models   3    
#sources      4    
#eff_ruptures 6,865
#tot_ruptures 6,865
#tot_weight   0    
============= =====

Informational data
------------------
=========================== =============================================================================
count_eff_ruptures.received tot 1.83 KB, max_per_task 644 B                                              
count_eff_ruptures.sent     sources 5.61 KB, param 2.91 KB, srcfilter 2.09 KB, monitor 984 B, gsims 454 B
hazard.input_weight         1964.5                                                                       
hazard.n_imts               1                                                                            
hazard.n_levels             19                                                                           
hazard.n_realizations       4                                                                            
hazard.n_sites              2                                                                            
hazard.n_sources            4                                                                            
hazard.output_weight        38.0                                                                         
hostname                    tstation.gem.lan                                                             
require_epsilons            False                                                                        
=========================== =============================================================================

Slowest sources
---------------
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
2      1         SimpleFaultSource 1,420        0.003     1         1        
0      2         AreaSource        1,815        0.002     1         1        
1      1         AreaSource        1,815        0.002     1         1        
1      3         AreaSource        1,815        0.001     1         1        
====== ========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
AreaSource        0.005     3     
SimpleFaultSource 0.003     1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.004 8.472E-04 0.003 0.004 3        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.042     0.0       1     
total count_eff_ruptures       0.011     0.0       3     
managing sources               0.003     0.0       1     
prefiltering source model      0.003     0.0       1     
store source_info              0.003     0.0       1     
aggregate curves               4.983E-05 0.0       3     
reading site collection        3.171E-05 0.0       1     
saving probability maps        2.670E-05 0.0       1     
============================== ========= ========= ======