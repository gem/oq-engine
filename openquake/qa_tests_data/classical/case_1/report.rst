Classical Hazard QA Test, Case 1
================================

============== ===================
checksum32     4_132_396_227      
date           2020-03-13T11:22:57
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 6, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                2.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      None              
pointsource_distance            {'default': {}}   
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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b11       1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.33333   3            3.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      P    3            0.00173   0.33333   3.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00173  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00239 NaN    0.00239 0.00239 1      
read_source_model  0.00113 NaN    0.00113 0.00113 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ======================================== ========
task              sent                                     received
read_source_model                                          1.56 KB 
preclassical      srcs=1.2 KB params=733 B srcfilter=223 B 369 B   
================= ======================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_67002                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.00876   0.0       1     
total preclassical          0.00239   1.64844   1     
store source_info           0.00208   0.0       1     
total read_source_model     0.00113   0.0       1     
aggregate curves            3.903E-04 0.0       1     
splitting/filtering sources 1.845E-04 0.0       1     
=========================== ========= ========= ======