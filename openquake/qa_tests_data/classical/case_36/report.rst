applyToSources with multiple sources
====================================

============== ===================
checksum32     3_235_130_248      
date           2020-03-13T11:22:51
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 1, num_rlzs = 9

Parameters
----------
=============================== ===================================================================================================================
calculation_mode                'preclassical'                                                                                                     
number_of_logic_tree_samples    9                                                                                                                  
maximum_distance                {'default': 30.0, 'Active Shallow Crust': 30.0, 'Subduction Interface': 100.0, 'Stable Continental Interior': 30.0}
investigation_time              1.0                                                                                                                
ses_per_logic_tree_path         1                                                                                                                  
truncation_level                None                                                                                                               
rupture_mesh_spacing            5.0                                                                                                                
complex_fault_mesh_spacing      50.0                                                                                                               
width_of_mfd_bin                0.5                                                                                                                
area_source_discretization      50.0                                                                                                               
pointsource_distance            {'default': 0}                                                                                                     
ground_motion_correlation_model None                                                                                                               
minimum_intensity               {}                                                                                                                 
random_seed                     42                                                                                                                 
master_seed                     0                                                                                                                  
ses_seed                        42                                                                                                                 
=============================== ===================================================================================================================

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
=============================================== ======= ================
smlt_path                                       weight  num_realizations
=============================================== ======= ================
b1_b211_b221_b231_b311_b321_b331_b341_b351_b361 0.55556 5               
b1_b212_b222_b232_b312_b322_b332_b342_b352_b362 0.11111 1               
b1_b213_b223_b233_b313_b323_b333_b343_b353_b363 0.33333 3               
=============================================== ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
2      '[SadighEtAl1997]' rrup      vs30       mag rake  
3      '[SadighEtAl1997]' rrup      vs30       mag rake  
4      '[SadighEtAl1997]' rrup      vs30       mag rake  
5      '[SadighEtAl1997]' rrup      vs30       mag rake  
6      '[SadighEtAl1997]' rrup      vs30       mag rake  
7      '[SadighEtAl1997]' rrup      vs30       mag rake  
8      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      NaN       7_318        0.0         
1      NaN       7_545        0.0         
2      NaN       7_107        0.0         
3      NaN       80           0.0         
4      NaN       100          0.0         
5      NaN       80           0.0         
6      0.01264   633          633         
7      0.01372   656          656         
8      0.01264   633          633         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         7      C    656          0.01395   0.01372   656         
1         8      C    633          0.01172   0.01264   633         
1         6      C    633          0.01052   0.01264   633         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.0      
C    0.03618  
S    0.0      
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.27093 0.48463 0.02086 1.31953 15     
read_source_model  0.28546 NaN     0.28546 0.28546 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= =============================================== ========
task              sent                                            received
read_source_model                                                 15.72 KB
preclassical      srcs=60.68 KB params=10.49 KB srcfilter=4.79 KB 4.9 KB  
================= =============================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66996                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          4.06398  3.29297   15    
splitting/filtering sources 3.72746  3.15234   15    
composite source model      1.04017  0.0       1     
total read_source_model     0.28546  0.0       1     
store source_info           0.00255  0.0       1     
aggregate curves            0.00110  0.0       3     
=========================== ======== ========= ======