QA test for blocksize independence (hazard)
===========================================

============== ===================
checksum32     3,254,196,570      
date           2018-04-30T11:22:55
engine_version 3.1.0-gitb0812f0   
============== ===================

num_sites = 2, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 400.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.5               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1024              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 2,625        5,572       
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         AreaSource   1,752        0.84714   0.08300    584       292       5     
2         AreaSource   582          0.30797   0.02661    194       97        155   
3         AreaSource   440          0.12611   0.02227    114       57        114   
9         AreaSource   222          0.00277   0.03023    3         2         4     
4         AreaSource   267          0.0       0.02529    0         0         0     
5         AreaSource   518          0.0       0.08577    0         0         0     
6         AreaSource   316          0.0       0.04673    0         0         0     
7         AreaSource   1,028        0.0       0.08702    0         0         0     
8         AreaSource   447          0.0       0.09025    0         0         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   1.28399   9     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
compute_ruptures   0.43896 0.08812 0.33728 0.49291 3        
================== ======= ======= ======= ======= =========

Informational data
------------------
================ ============================================================================ ========
task             sent                                                                         received
compute_ruptures sources=132.24 KB src_filter=2.26 KB param=1.71 KB monitor=990 B gsims=381 B 30.71 KB
================ ============================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         1.31689   3.35547   3     
managing sources               0.62188   0.0       1     
reading composite source model 0.51119   0.0       1     
splitting sources              0.49852   0.0       1     
saving ruptures                0.00608   0.0       3     
store source_info              0.00543   0.0       1     
making contexts                0.00495   0.0       5     
setting event years            0.00176   0.0       1     
unpickling compute_ruptures    0.00147   0.0       3     
reading site collection        2.501E-04 0.0       1     
============================== ========= ========= ======