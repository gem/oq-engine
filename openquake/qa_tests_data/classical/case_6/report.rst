Classical Hazard QA Test, Case 6
================================

============== ===================
checksum32     3,056,992,103      
date           2019-09-24T15:21:15
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.1               
complex_fault_mesh_spacing      0.1               
width_of_mfd_bin                1.0               
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
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 140          140         
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
1         0      S    91           0.00334   1.00000   91           27,218
2         0      C    49           0.00246   1.00000   49           19,894
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.00246   1     
S    0.00334   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.00341 6.174E-04 0.00298 0.00385 2      
read_source_models 0.12033 NaN       0.12033 0.12033 1      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ============================================= ========
task               sent                                          received
preclassical       srcs=2.25 KB srcfilter=1.26 KB params=1.01 KB 684 B   
read_source_models converter=314 B fnames=106 B                  2.04 KB 
================== ============================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1816                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.12033   0.44922   1     
total preclassical       0.00683   0.0       2     
store source_info        0.00253   0.0       1     
aggregate curves         5.651E-04 0.0       2     
managing sources         3.712E-04 0.0       1     
======================== ========= ========= ======