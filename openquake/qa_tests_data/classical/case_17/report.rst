Classical Hazard QA Test, Case 17
=================================

============== ===================
checksum32     575,048,364        
date           2018-02-25T06:42:46
engine_version 2.10.0-git1f7c0c0  
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    5                 
maximum_distance                {'default': 200.0}
investigation_time              1000.0            
ses_per_logic_tree_path         1                 
truncation_level                2.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     106               
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
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        0.200  trivial(1)      3/1             
b2        0.200  trivial(1)      2/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=5)
  0,SadighEtAl1997(): [0 1 2]
  1,SadighEtAl1997(): [3 4]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 46           39          
source_model_2.xml 1      Active Shallow Crust 46           7           
================== ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 92   
#tot_ruptures 46   
#tot_weight   4.600
============= =====

Informational data
------------------
======================= =========================================================================
count_ruptures.received max_per_task 899 B, tot 899 B                                            
count_ruptures.sent     sources 1.78 KB, srcfilter 722 B, param 418 B, monitor 330 B, gsims 120 B
hazard.input_weight     13.100000000000001                                                       
hazard.n_imts           1                                                                        
hazard.n_levels         3                                                                        
hazard.n_realizations   5                                                                        
hazard.n_sites          1                                                                        
hazard.n_sources        2                                                                        
hazard.output_weight    3.0                                                                      
hostname                tstation.gem.lan                                                         
require_epsilons        False                                                                    
======================= =========================================================================

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
2         PointSource  7            3.581E-04 3         2        
1         PointSource  39           2.701E-04 3         2        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  6.282E-04 2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.004 NaN    0.004 0.004 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total count_ruptures           0.004     0.0       1     
store source_info              0.004     0.0       1     
reading composite source model 0.003     0.0       1     
managing sources               0.003     0.0       1     
reading site collection        5.627E-05 0.0       1     
saving probability maps        3.099E-05 0.0       1     
aggregate curves               2.551E-05 0.0       1     
============================== ========= ========= ======