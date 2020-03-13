Classical Hazard QA Test, Case 11
=================================

============== ===================
checksum32     1_315_577_391      
date           2020-03-13T11:23:06
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 3

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
b1_b2     0.20000 1               
b1_b3     0.60000 1               
b1_b4     0.20000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
2      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      2.857E-04 3_500        3_500       
1      3.333E-04 3_000        3_000       
2      4.000E-04 2_500        2_500       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      P    3_500        0.01282   2.857E-04 3_500       
1         2      P    2_500        0.01110   4.000E-04 2_500       
1         1      P    3_000        0.00976   3.333E-04 3_000       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.03368  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.01236 0.00151 0.01079 0.01382 3      
read_source_model  0.00416 NaN     0.00416 0.00416 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= =========================================== ========
task              sent                                        received
read_source_model                                             1.48 KB 
preclassical      srcs=3.44 KB params=1.89 KB srcfilter=669 B 1.08 KB 
================= =========================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_67008                  time_sec memory_mb counts
=========================== ======== ========= ======
composite source model      0.04533  0.0       1     
total preclassical          0.03707  0.48828   3     
total read_source_model     0.00416  0.0       1     
store source_info           0.00208  0.0       1     
aggregate curves            0.00191  0.0       3     
splitting/filtering sources 0.00124  0.0       3     
=========================== ======== ========= ======