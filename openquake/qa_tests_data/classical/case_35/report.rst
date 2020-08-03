Classical Hazard QA Test, Case 35 - Cluster model
=================================================

============== ===================
checksum32     2_090_330_762      
date           2020-03-13T11:22:13
engine_version 3.9.0-gitfb3ef3a732
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
0      1.00000   2            2.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
0         0      X    1            0.00248   1.00000   1.00000     
1         0      X    1            1.960E-04 1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
X    0.00268  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00406 NaN    0.00406 0.00406 1      
read_source_model  0.00659 NaN    0.00659 0.00659 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model                                           3.5 KB  
preclassical      srcs=4.46 KB params=654 B srcfilter=223 B 409 B   
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66987                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.01846   0.0       1     
total read_source_model     0.00659   0.0       1     
total preclassical          0.00406   0.0       1     
store source_info           0.00299   0.0       1     
splitting/filtering sources 3.769E-04 0.0       1     
aggregate curves            2.737E-04 0.0       1     
=========================== ========= ========= ======