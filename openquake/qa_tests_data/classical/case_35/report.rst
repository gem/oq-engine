Classical Hazard QA Test, Case 35 - Cluster model
=================================================

============== ===================
checksum32     1,518,465,114      
date           2019-09-24T15:21:17
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 1, num_levels = 5, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                10.0              
rupture_mesh_spacing            10.0              
complex_fault_mesh_spacing      10.0              
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
b11       1.00000 trivial(1)      1               
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
source_model.xml 0      Active Shallow Crust 2            2           
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
0         0      X    1            0.00151   1.00000   1.00000      662  
1         0      X    1            0.00116   1.00000   1.00000      861  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.00267   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
classical          0.04072 NaN    0.04072 0.04072 1      
read_source_models 0.01090 NaN    0.01090 0.01090 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ========================================= ========
task               sent                                      received
classical          group=3.4 KB src_filter=647 B param=533 B 1.3 KB  
read_source_models converter=314 B fnames=107 B              3.57 KB 
================== ========================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1825                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          0.04072   0.0       1     
aggregate curves         0.01299   0.0       1     
total read_source_models 0.01090   0.0       1     
store source_info        0.00263   0.0       1     
make_contexts            6.044E-04 0.0       2     
computing mean_std       3.784E-04 0.0       2     
get_poes                 3.510E-04 0.0       2     
managing sources         3.257E-04 0.0       1     
======================== ========= ========= ======