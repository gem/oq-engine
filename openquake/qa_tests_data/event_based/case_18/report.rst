Event-Based Hazard QA Test, Case 18
===================================

============== ===================
checksum32     3_365_178_779      
date           2020-03-13T11:21:40
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 3

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    3                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         350               
truncation_level                0.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.001             
area_source_discretization      20.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1064              
master_seed                     0                 
ses_seed                        1064              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `three_gsim_logic_tree.xml <three_gsim_logic_tree.xml>`_    
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 3               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================== ================= ======================= =================
grp_id gsims                                                          distances         siteparams              ruptparams       
====== ============================================================== ================= ======================= =================
0      '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ============================================================== ================= ======================= =================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3.333E-04 3_000        3_000       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      P    3_000        0.00523   3.333E-04 3_000       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00523  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00590 NaN    0.00590 0.00590 1      
read_source_model  0.00436 NaN    0.00436 0.00436 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ===================================== ========
task              sent                                  received
read_source_model                                       1.49 KB 
preclassical      srcs=1.14 KB params=646 B gsims=385 B 370 B   
================= ===================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66952                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.02053   0.0       1     
total preclassical          0.00590   2.02734   1     
total read_source_model     0.00436   0.0       1     
store source_info           0.00216   0.0       1     
aggregate curves            4.354E-04 0.0       1     
splitting/filtering sources 2.184E-04 0.18750   1     
=========================== ========= ========= ======