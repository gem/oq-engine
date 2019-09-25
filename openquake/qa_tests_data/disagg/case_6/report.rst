GEM model for PAC, 0.10 in 50 years, Suva, testing IDL
======================================================

============== ===================
checksum32     2,604,004,363      
date           2019-09-24T15:20:58
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 1, num_levels = 20, num_rlzs = 3

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ========================
Name                    File                    
======================= ========================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_
job_ini                 `job.ini <job.ini>`_    
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_
======================= ========================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(3,0,0)   3               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ======================= ============================
grp_id gsims                                                         distances   siteparams              ruptparams                  
====== ============================================================= =========== ======================= ============================
0      '[BooreAtkinson2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
====== ============================================================= =========== ======================= ============================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=9, rlzs=3)>

Number of ruptures per tectonic region type
-------------------------------------------
============================== ====== ==================== ============ ============
source_model                   grp_id trt                  eff_ruptures tot_ruptures
============================== ====== ==================== ============ ============
ssm/shallow/shallow_faults.xml 0      Active Shallow Crust 349          349         
============================== ====== ==================== ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
32        0      S    80           0.02650   1.00000   80           3,018
19        0      S    86           0.02603   1.00000   86           3,304
36        0      S    67           0.02491   1.00000   67           2,689
39        0      S    61           0.02310   1.00000   61           2,641
28        0      S    55           0.01952   1.00000   55           2,818
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.12007   5     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.02445 0.00282 0.01998 0.02692 5      
read_source_models 0.07620 NaN     0.07620 0.07620 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================== ========
task               sent                                           received
preclassical       srcs=31.08 KB params=3.71 KB srcfilter=3.28 KB 1.67 KB 
read_source_models converter=314 B fnames=117 B                   28.38 KB
================== ============================================== ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1736                time_sec  memory_mb counts
======================== ========= ========= ======
total preclassical       0.12226   0.24609   5     
total read_source_models 0.07620   0.22656   1     
store source_info        0.00256   0.0       1     
aggregate curves         0.00178   0.0       5     
managing sources         3.850E-04 0.0       1     
======================== ========= ========= ======