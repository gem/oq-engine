Event-based PSHA with logic tree sampling
=========================================

============== ===================
checksum32     3,756,725,912      
date           2018-03-26T15:56:51
engine_version 2.10.0-git543cfb0  
============== ===================

num_sites = 3, num_levels = 38

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    10                
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         40                
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        23                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model1.xml <source_model1.xml>`_                    
source                  `source_model2.xml <source_model2.xml>`_                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b11       0.100  simple(3)       4/3             
b12       0.100  simple(3)       6/3             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ============================= =================
grp_id gsims                                                         distances   siteparams                    ruptparams       
====== ============================================================= =========== ============================= =================
0      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
1      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
====== ============================================================= =========== ============================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=10)
  0,BooreAtkinson2008(): [1]
  0,CampbellBozorgnia2008(): [2]
  0,ChiouYoungs2008(): [0 3]
  1,BooreAtkinson2008(): [4 5 6 7 9]
  1,CampbellBozorgnia2008(): [8]>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== ============ ============
source_model      grp_id trt                  eff_ruptures tot_ruptures
================= ====== ==================== ============ ============
source_model1.xml 0      Active Shallow Crust 2,456        2,456       
source_model2.xml 1      Active Shallow Crust 2,456        2,456       
================= ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 4,912
#tot_ruptures 4,912
#tot_weight   0    
============= =====

Slowest sources
---------------
========= ============ ============ ========= ========== ========= =========
source_id source_class num_ruptures calc_time split_time num_sites num_split
========= ============ ============ ========= ========== ========= =========
1         AreaSource   2,456        0.0       0.057      0         0        
========= ============ ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.868 0.311  0.412 1.191 6        
================== ===== ====== ===== ===== =========

Informational data
------------------
================ =============================================================================== ========
task             sent                                                                            received
compute_ruptures sources=159.13 KB param=5.5 KB src_filter=4.86 KB monitor=1.93 KB gsims=1.88 KB 3.16 MB 
================ =============================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         5.208     2.645     6     
making contexts                1.924     0.0       2,667 
managing sources               1.418     0.0       1     
reading composite source model 0.259     0.0       1     
unpickling compute_ruptures    0.229     0.0       6     
saving ruptures                0.119     0.0       6     
splitting sources              0.117     0.0       1     
setting event years            0.049     0.0       1     
store source_info              0.003     0.0       1     
reading site collection        3.574E-04 0.0       1     
============================== ========= ========= ======