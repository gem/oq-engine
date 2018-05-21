QA test for blocksize independence (hazard)
===========================================

============== ===================
checksum32     3,254,196,570      
date           2018-05-15T04:14:17
engine_version 3.1.0-git0acbc11   
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
1         PointSource  6            0.87342   0.0        584       292       5     
2         PointSource  6            0.30947   0.0        194       97        155   
3         PointSource  5            0.13355   0.0        114       57        114   
9         PointSource  3            0.00333   0.0        3         2         0     
4         PointSource  3            0.0       0.0        0         0         0     
5         PointSource  2            0.0       0.0        0         0         0     
6         PointSource  2            0.0       0.0        0         0         0     
7         PointSource  4            0.0       0.0        0         0         0     
8         PointSource  3            0.0       0.0        0         0         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  1.31977   9     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.00910 0.00607 0.00308 0.03000 59       
compute_ruptures   0.25180 0.24030 0.01947 0.52791 6        
================== ======= ======= ======= ======= =========

Informational data
------------------
================ ============================================================================== ========
task             sent                                                                           received
prefilter        srcs=392.08 KB monitor=18.61 KB srcfilter=13.19 KB                             149 KB  
compute_ruptures sources=343.83 KB src_filter=4.52 KB param=3.42 KB monitor=1.93 KB gsims=762 B 31.85 KB
================ ============================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         1.51082   1.14844   6     
managing sources               0.83419   0.0       1     
reading composite source model 0.66274   0.0       1     
total prefilter                0.53669   3.43359   59    
splitting sources              0.53152   0.0       1     
unpickling prefilter           0.01152   0.0       59    
saving ruptures                0.01121   0.0       6     
store source_info              0.00686   0.0       1     
making contexts                0.00480   0.0       5     
setting event years            0.00207   0.0       1     
unpickling compute_ruptures    0.00180   0.0       6     
reading site collection        3.743E-04 0.0       1     
============================== ========= ========= ======