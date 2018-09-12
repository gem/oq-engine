Classical Hazard QA Test, Case 1
================================

============== ===================
checksum32     1,984,592,463      
date           2018-09-05T10:04:38
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 1, num_levels = 6

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                2.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
=============== ============================================
Name            File                                        
=============== ============================================
gsim_logic_tree `gsim_logic_tree.xml <gsim_logic_tree.xml>`_
job_ini         `job.ini <job.ini>`_                        
source          `source_model.xml <source_model.xml>`_      
source_model    `source_model.xml <source_model.xml>`_      
=============== ============================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

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
source_model.xml 0      Active Shallow Crust 1            1           
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  1            0.00276   4.530E-06  1.00000   1         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.00276   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ========= ====== ========= ========= =========
operation-duration   mean      stddev min       max       num_tasks
pickle_source_models 0.00164   NaN    0.00164   0.00164   1        
count_eff_ruptures   0.00338   NaN    0.00338   0.00338   1        
preprocess           4.759E-04 NaN    4.759E-04 4.759E-04 1        
==================== ========= ====== ========= ========= =========

Fastest task
------------
taskno=1, weight=0, duration=0 s, sources="1"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 NaN    1       1       1
weight   0.10000 NaN    0.10000 0.10000 1
======== ======= ====== ======= ======= =

Slowest task
------------
taskno=1, weight=0, duration=0 s, sources="1"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 NaN    1       1       1
weight   0.10000 NaN    0.10000 0.10000 1
======== ======= ====== ======= ======= =

Data transfer
-------------
==================== ==================================================================== ========
task                 sent                                                                 received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                 155 B   
count_eff_ruptures   sources=1.3 KB param=601 B monitor=307 B srcfilter=220 B gsims=120 B 358 B   
preprocess           srcs=0 B srcfilter=0 B param=0 B monitor=0 B                         1.22 KB 
==================== ==================================================================== ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
managing sources           0.00947   0.0       1     
store source_info          0.00343   0.0       1     
total count_eff_ruptures   0.00338   0.0       1     
total pickle_source_models 0.00164   0.0       1     
total preprocess           4.759E-04 0.0       1     
splitting sources          3.526E-04 0.0       1     
aggregate curves           1.755E-04 0.0       1     
========================== ========= ========= ======