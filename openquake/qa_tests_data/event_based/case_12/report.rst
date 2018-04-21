Event Based QA Test, Case 12
============================

============== ===================
checksum32     3,009,527,013      
date           2018-04-19T05:04:16
engine_version 3.1.0-git9c5da5b   
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         3500              
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1066              
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
b1        1.000  trivial(1,1)    1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      SadighEtAl1997()    rrup      vs30       mag rake  
1      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,SadighEtAl1997(): [0]
  1,BooreAtkinson2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1.000        1           
source_model.xml 1      Stable Continental   1.000        1           
================ ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 2.000
#tot_ruptures 2    
#tot_weight   0    
============= =====

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
2         PointSource  1            0.035     1.669E-06  1         1         3,370 
1         PointSource  1            0.031     5.960E-06  1         1         3,536 
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.066     2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.037 0.004  0.034 0.040 2        
================== ===== ====== ===== ===== =========

Informational data
------------------
================ ========================================================================== =========
task             sent                                                                       received 
compute_ruptures sources=2.63 KB src_filter=1.41 KB param=1.14 KB monitor=660 B gsims=251 B 179.83 KB
================ ========================================================================== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.100     0.0       1     
total compute_ruptures         0.074     3.449     2     
saving ruptures                0.045     0.0       2     
setting event years            0.015     0.0       1     
store source_info              0.006     0.0       1     
reading composite source model 0.005     0.0       1     
making contexts                0.003     0.0       2     
unpickling compute_ruptures    7.095E-04 0.0       2     
splitting sources              3.977E-04 0.0       1     
reading site collection        2.437E-04 0.0       1     
============================== ========= ========= ======