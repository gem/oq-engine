applyToSources with multiple sources
====================================

============== ===================
checksum32     3,235,130,248      
date           2019-10-01T06:32:41
engine_version 3.8.0-git66affb82eb
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
=============================================== ======= =============== ================
smlt_path                                       weight  gsim_logic_tree num_realizations
=============================================== ======= =============== ================
b1_b211_b221_b231_b311_b321_b331_b341_b351_b361 0.11111 trivial(0,0,1)  1               
b1_b212_b222_b232_b312_b322_b332_b342_b352_b362 0.11111 trivial(0,0,1)  1               
b1_b213_b223_b233_b313_b323_b333_b343_b353_b363 0.11111 trivial(0,0,1)  1               
=============================================== ======= =============== ================

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

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=9)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.0       80           0.0         
1      1.00000   633          633         
2      0.0       7,318        0.0         
3      0.0       100          0.0         
4      1.00000   656          656         
5      0.0       7,545        0.0         
6      0.0       80           0.0         
7      1.00000   633          633         
8      0.0       7,107        0.0         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
1         7      C    633          0.00701   1.00000   633          90,337 
1         1      C    633          0.00501   1.00000   633          126,248
1         4      C    656          0.00373   1.00000   656          175,824
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       21    
C    0.01575   3     
S    0.0       9     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.45302 0.02325 0.42977 0.47626 3      
preclassical       0.00573 0.00327 0.00145 0.01054 18     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =============================================== ========
task         sent                                            received
SourceReader apply_unc=10.92 KB ltmodel=753 B fname=312 B    90.24 KB
preclassical srcs=57.49 KB params=10.49 KB srcfilter=5.73 KB 5.28 KB 
============ =============================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_6485              time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     1.35907  0.69141   3     
composite source model 0.51270  0.0       1     
total preclassical     0.10318  0.0       18    
aggregate curves       0.00430  0.0       18    
store source_info      0.00254  0.0       1     
====================== ======== ========= ======