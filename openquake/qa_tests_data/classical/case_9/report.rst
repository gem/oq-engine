Classical Hazard QA Test, Case 9
================================

============== ===================
checksum32     3_616_596_807      
date           2020-03-13T11:22:13
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.01              
complex_fault_mesh_spacing      0.01              
width_of_mfd_bin                0.001             
area_source_discretization      10.0              
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
b1_b2     0.50000 1               
b1_b3     0.50000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3.333E-04 3_000        3_000       
1      2.857E-04 3_500        3_500       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         1      P    3_500        0.01305   2.857E-04 3_500       
1         0      P    3_000        0.00720   3.333E-04 3_000       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.02026  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.01110 0.00432 0.00805 0.01416 2      
read_source_model  0.00536 NaN     0.00536 0.00536 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= =========================================== ========
task              sent                                        received
read_source_model                                             1.48 KB 
preclassical      srcs=2.29 KB params=1.26 KB srcfilter=446 B 740 B   
================= =========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66989                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.04586   0.0       1     
total preclassical          0.02221   0.51953   2     
total read_source_model     0.00536   0.0       1     
store source_info           0.00256   0.0       1     
splitting/filtering sources 6.738E-04 0.0       2     
aggregate curves            5.505E-04 0.0       2     
=========================== ========= ========= ======