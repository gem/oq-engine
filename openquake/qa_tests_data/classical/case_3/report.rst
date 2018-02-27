Classical Hazard QA Test, Case 3
================================

============== ===================
checksum32     4,051,148,706      
date           2018-02-25T06:42:51
engine_version 2.10.0-git1f7c0c0  
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      0.05              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  trivial(1)      1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 31,353       31,353      
================ ====== ==================== ============ ============

Informational data
------------------
======================= =================================================================================
count_ruptures.received tot 16.13 KB, max_per_task 826 B                                                 
count_ruptures.sent     sources 6.28 MB, srcfilter 14.1 KB, param 8.16 KB, monitor 6.45 KB, gsims 2.34 KB
hazard.input_weight     3135.3                                                                           
hazard.n_imts           1                                                                                
hazard.n_levels         3                                                                                
hazard.n_realizations   1                                                                                
hazard.n_sites          1                                                                                
hazard.n_sources        1                                                                                
hazard.output_weight    3.0                                                                              
hostname                tstation.gem.lan                                                                 
require_epsilons        False                                                                            
======================= =================================================================================

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
1         AreaSource   31,353       4.132     31,354    31,353   
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   4.132     1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.284 0.018  0.236 0.305 20       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 7.622     0.0       1     
managing sources               6.459     0.0       1     
total count_ruptures           5.686     3.438     20    
store source_info              0.003     0.0       1     
aggregate curves               3.216E-04 0.0       20    
reading site collection        4.363E-05 0.0       1     
saving probability maps        2.885E-05 0.0       1     
============================== ========= ========= ======