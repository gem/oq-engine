Event-based PSHA with logic tree sampling
=========================================

============== ===================
checksum32     3,756,725,912      
date           2018-09-05T10:04:02
engine_version 3.2.0-gitb4ef3a4b6c
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b11       0.10000 simple(3)       4/3             
b12       0.10000 simple(3)       6/3             
========= ======= =============== ================

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
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         AreaSource   2,456        11        0.05760    2.05863   614       9,057 
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   11        1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ======= ======= ======= =========
operation-duration   mean    stddev  min     max     num_tasks
pickle_source_models 0.06407 0.01124 0.05612 0.07202 2        
preprocess           0.19699 0.03240 0.11319 0.27431 62       
compute_gmfs         0.46450 0.10030 0.15836 0.67015 64       
==================== ======= ======= ======= ======= =========

Data transfer
-------------
==================== ====================================================================================================== ========
task                 sent                                                                                                   received
pickle_source_models monitor=618 B converter=578 B fnames=368 B                                                             318 B   
preprocess           srcs=222.1 KB param=29.37 KB monitor=19.31 KB srcfilter=15.32 KB                                       3.46 MB 
compute_gmfs         sources_or_ruptures=3.52 MB param=214.94 KB rlzs_by_gsim=32.63 KB monitor=19.19 KB src_filter=13.75 KB 3.91 MB 
==================== ====================================================================================================== ========

Slowest operations
------------------
========================== ======== ========= ======
operation                  time_sec memory_mb counts
========================== ======== ========= ======
total compute_gmfs         29       0.46094   64    
building hazard            28       0.43359   64    
total preprocess           12       0.0       62    
making contexts            3.10443  0.0       2,667 
saving ruptures            2.10637  0.0       604   
GmfGetter.init             0.36668  0.43359   64    
managing sources           0.20208  0.0       1     
saving gmfs                0.18722  0.0       64    
building ruptures          0.17536  0.0       64    
building hazard curves     0.16332  0.0       769   
total pickle_source_models 0.12813  0.89062   2     
splitting sources          0.11911  0.0       1     
aggregating hcurves        0.03722  0.0       64    
store source_info          0.00441  0.0       1     
saving gmf_data/indices    0.00174  0.0       1     
========================== ======== ========= ======