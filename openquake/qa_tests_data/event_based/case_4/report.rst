Event-Based Hazard QA Test, Case 4
==================================

============== ===================
checksum32     2_277_314_350      
date           2020-03-13T11:21:00
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         50                
truncation_level                0.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1066              
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
b1        1.00000 1               
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
0      0.20000   5            5.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      S    5            0.00594   0.20000   5.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.00594  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00723 NaN    0.00723 0.00723 1      
read_source_model  0.00246 NaN    0.00246 0.00246 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ======================================== ========
task              sent                                     received
read_source_model                                          1.45 KB 
preclassical      srcs=1.3 KB params=638 B srcfilter=223 B 369 B   
================= ======================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66930                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.01237   0.0       1     
total preclassical          0.00723   0.48828   1     
total read_source_model     0.00246   0.0       1     
store source_info           0.00220   0.0       1     
splitting/filtering sources 4.182E-04 0.0       1     
aggregate curves            2.429E-04 0.0       1     
=========================== ========= ========= ======