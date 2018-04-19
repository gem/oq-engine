Classical Hazard QA Test, Case 17
=================================

============== ===================
checksum32     575,048,364        
date           2018-04-19T05:02:32
engine_version 3.1.0-git9c5da5b   
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

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  39           6.626E-04 8.345E-06  2         2         0     
2         PointSource  7            2.761E-04 3.099E-06  2         2         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  9.387E-04 2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.003 NaN    0.003 0.003 1        
================== ===== ====== ===== ===== =========

Informational data
------------------
============== ===================================================================== ========
task           sent                                                                  received
count_ruptures sources=1.78 KB srcfilter=722 B param=418 B monitor=330 B gsims=120 B 441 B   
============== ===================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.008     0.0       1     
store source_info              0.006     0.0       1     
managing sources               0.004     0.0       1     
total count_ruptures           0.003     2.043     1     
splitting sources              5.419E-04 0.0       1     
reading site collection        2.589E-04 0.0       1     
unpickling count_ruptures      6.509E-05 0.0       1     
saving probability maps        3.839E-05 0.0       1     
aggregate curves               3.409E-05 0.0       1     
============================== ========= ========= ======