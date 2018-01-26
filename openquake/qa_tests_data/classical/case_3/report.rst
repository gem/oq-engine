Classical Hazard QA Test, Case 3
================================

============== ===================
checksum32     4,051,148,706      
date           2018-01-11T04:54:28
engine_version 2.9.0-git3c583c4   
============== ===================

num_sites = 1, num_imts = 1

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
random_seed                     1066              
master_seed                     0                 
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
======================= ==================================================================================
count_ruptures.received tot 1009.17 KB, max_per_task 65.06 KB                                             
count_ruptures.sent     sources 6.28 MB, srcfilter 11.28 KB, param 6.53 KB, monitor 4.98 KB, gsims 1.42 KB
hazard.input_weight     3135.3                                                                            
hazard.n_imts           1                                                                                 
hazard.n_levels         3                                                                                 
hazard.n_realizations   1                                                                                 
hazard.n_sites          1                                                                                 
hazard.n_sources        1                                                                                 
hazard.output_weight    3.0                                                                               
hostname                tstation.gem.lan                                                                  
require_epsilons        False                                                                             
======================= ==================================================================================

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
1         AreaSource   31,353       2.011     1         31,353   
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   2.011     1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.155 0.025  0.097 0.186 16       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 7.403     0.0       1     
managing sources               6.246     0.0       1     
total count_ruptures           2.477     4.422     16    
aggregate curves               0.030     0.0       16    
store source_info              0.004     0.0       1     
reading site collection        5.293E-05 0.0       1     
saving probability maps        3.004E-05 0.0       1     
============================== ========= ========= ======