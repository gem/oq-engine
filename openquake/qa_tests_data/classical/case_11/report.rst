Classical Hazard QA Test, Case 11
=================================

============== ===================
checksum32     3,151,174,296      
date           2018-09-05T10:04:41
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 1, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.01              
complex_fault_mesh_spacing      0.01              
width_of_mfd_bin                0.001             
area_source_discretization      10.0              
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1_b2     0.20000 trivial(1)      1/1             
b1_b3     0.60000 trivial(1)      1/1             
b1_b4     0.20000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
2      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,SadighEtAl1997(): [0]
  1,SadighEtAl1997(): [1]
  2,SadighEtAl1997(): [2]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3,500        3,000       
source_model.xml 1      Active Shallow Crust 3,000        3,000       
source_model.xml 2      Active Shallow Crust 2,500        3,000       
================ ====== ==================== ============ ============

============= =====
#TRT models   3    
#eff_ruptures 9,000
#tot_ruptures 9,000
#tot_weight   900  
============= =====

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  2,500        0.00716   1.192E-06  1.00000   3         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.00716   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ========= ======= ======= =========
operation-duration   mean    stddev    min     max     num_tasks
pickle_source_models 0.00524 NaN       0.00524 0.00524 1        
count_eff_ruptures   0.00298 7.405E-04 0.00212 0.00342 3        
preprocess           0.00751 0.00187   0.00542 0.00904 3        
==================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=2, weight=300, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   300     NaN    300 300 1
======== ======= ====== === === =

Slowest task
------------
taskno=1, weight=350, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   350     NaN    350 350 1
======== ======= ====== === === =

Data transfer
-------------
==================== ======================================================================= ========
task                 sent                                                                    received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                    156 B   
count_eff_ruptures   sources=3.93 KB param=1.51 KB monitor=921 B srcfilter=660 B gsims=360 B 1.05 KB 
preprocess           srcs=3.45 KB monitor=957 B srcfilter=759 B param=108 B                  3.71 KB 
==================== ======================================================================= ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
managing sources           0.02410   0.0       1     
total preprocess           0.02252   0.0       3     
total count_eff_ruptures   0.00894   0.0       3     
total pickle_source_models 0.00524   0.0       1     
store source_info          0.00423   0.0       1     
aggregate curves           5.732E-04 0.0       3     
splitting sources          2.913E-04 0.0       1     
========================== ========= ========= ======