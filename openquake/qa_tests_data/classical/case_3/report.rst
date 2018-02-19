Classical Hazard QA Test, Case 3
================================

============== ===================
checksum32     4,051,148,706      
date           2018-02-19T09:59:02
engine_version 2.9.0-gitb536198   
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
======================= ===================================================================================
count_ruptures.received tot 25.43 KB, max_per_task 815 B                                                   
count_ruptures.sent     sources 6.29 MB, srcfilter 22.56 KB, param 13.06 KB, monitor 9.97 KB, gsims 3.75 KB
hazard.input_weight     3135.3                                                                             
hazard.n_imts           1                                                                                  
hazard.n_levels         3                                                                                  
hazard.n_realizations   1                                                                                  
hazard.n_sites          1                                                                                  
hazard.n_sources        1                                                                                  
hazard.output_weight    3.0                                                                                
hostname                tstation.gem.lan                                                                   
require_epsilons        False                                                                              
======================= ===================================================================================

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
1         AreaSource   31,353       2.536     31,354    31,353   
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   2.536     1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.105 0.034  0.029 0.181 32       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 7.792     0.0       1     
managing sources               6.833     0.0       1     
total count_ruptures           3.353     1.809     32    
store source_info              0.004     0.0       1     
aggregate curves               5.016E-04 0.0       32    
reading site collection        4.125E-05 0.0       1     
saving probability maps        2.909E-05 0.0       1     
============================== ========= ========= ======