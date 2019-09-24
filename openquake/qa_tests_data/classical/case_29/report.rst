NNParametric
============

============== ===================
checksum32     34,932,175         
date           2019-09-24T15:21:15
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 1, num_levels = 19, num_rlzs = 1

Parameters
----------
=============================== =================================
calculation_mode                'preclassical'                   
number_of_logic_tree_samples    0                                
maximum_distance                {'default': [(5, 500), (6, 500)]}
investigation_time              1.0                              
ses_per_logic_tree_path         1                                
truncation_level                2.0                              
rupture_mesh_spacing            2.0                              
complex_fault_mesh_spacing      2.0                              
width_of_mfd_bin                0.1                              
area_source_discretization      5.0                              
ground_motion_correlation_model None                             
minimum_intensity               {}                               
random_seed                     23                               
master_seed                     0                                
ses_seed                        42                               
=============================== =================================

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
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
====== ===================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            1           
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
test      0      N    1            9.773E-04 1.00000   1.00000      1,023
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    9.773E-04 1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00149 NaN    0.00149 0.00149 1      
read_source_models 0.00257 NaN    0.00257 0.00257 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ========================================= ========
task               sent                                      received
preclassical       srcs=1.83 KB srcfilter=661 B params=647 B 342 B   
read_source_models converter=314 B fnames=107 B              2.28 KB 
================== ========================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1814                time_sec  memory_mb counts
======================== ========= ========= ======
store source_info        0.00305   1.03125   1     
total read_source_models 0.00257   0.0       1     
total preclassical       0.00149   0.0       1     
managing sources         3.827E-04 0.0       1     
aggregate curves         2.613E-04 0.0       1     
======================== ========= ========= ======