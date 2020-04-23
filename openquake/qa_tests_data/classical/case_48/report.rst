Finite-size effects
===================

============== ===================
checksum32     1_799_846_366      
date           2020-04-23T06:19:14
engine_version 3.9.0-git511b3c2c31
============== ===================

num_sites = 2, num_levels = 20, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 110.0}
investigation_time              100.0             
ses_per_logic_tree_path         1                 
truncation_level                2.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      None              
pointsource_distance            None              
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

Slowest sources
---------------
========= ==== =========== ========= ========= ============
source_id code num_sources calc_time num_sites eff_ruptures
========= ==== =========== ========= ========= ============
1         P    1           0.00169   0.20000   10          
========= ==== =========== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00169  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00241 NaN    0.00241 0.00241 1      
read_source_model  0.00200 NaN    0.00200 0.00200 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model                                           1.44 KB 
preclassical      srcs=1.14 KB params=824 B srcfilter=223 B 392 B   
classical                                                   0 B     
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_47245                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.05823   0.97656   1     
total preclassical          0.00241   1.16016   1     
total read_source_model     0.00200   0.02734   1     
store source_info           0.00100   0.0       1     
aggregate curves            6.974E-04 0.0       1     
splitting/filtering sources 2.520E-04 0.0       1     
=========================== ========= ========= ======