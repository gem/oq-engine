Classical PSHA-Based Hazard
===========================

============== ===================
checksum32     1,041,255,436      
date           2018-06-26T14:57:04
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 1, num_levels = 20

Parameters
----------
=============================== ==================
calculation_mode                'classical_damage'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job_haz.ini <job_haz.ini>`_                                
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_fragility    `fragility_model.xml <fragility_model.xml>`_                
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
source_model.xml 0      Active Shallow Crust 482          482         
================ ====== ==================== ============ ============

Exposure model
--------------
=============== ========
#assets         1       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
Wood     1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
1         SimpleFaultSource 482          0.03978   2.079E-04  1.00000   15        0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.03978   1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.00803 0.00299   0.00299 0.01152 15       
count_eff_ruptures 0.00878 7.845E-04 0.00820 0.01009 6        
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=5, weight=85, duration=0 s, sources="1"

======== ======= ======= === === =
variable mean    stddev  min max n
======== ======= ======= === === =
nsites   1.00000 0.0     1   1   2
weight   42      3.53553 40  45  2
======== ======= ======= === === =

Slowest task
------------
taskno=4, weight=90, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 0.0    1   1   2
weight   45      0.0    45  45  2
======== ======= ====== === === =

Data transfer
-------------
================== ============================================================================ ========
task               sent                                                                         received
RtreeFilter        srcs=15.36 KB monitor=4.72 KB srcfilter=4.09 KB                              17 KB   
count_eff_ruptures sources=10.68 KB param=3.33 KB monitor=1.93 KB srcfilter=1.44 KB gsims=720 B 2.1 KB  
================== ============================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.23780   0.0       1     
total prefilter                0.12052   4.74219   15    
total count_eff_ruptures       0.05268   6.39844   6     
store source_info              0.00745   0.0       1     
reading composite source model 0.00610   0.0       1     
unpickling prefilter           0.00423   0.0       15    
aggregate curves               0.00206   0.0       6     
unpickling count_eff_ruptures  0.00186   0.0       6     
reading site collection        0.00100   0.0       1     
reading exposure               7.064E-04 0.0       1     
splitting sources              5.028E-04 0.0       1     
============================== ========= ========= ======