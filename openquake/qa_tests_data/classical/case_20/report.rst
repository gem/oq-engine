Classical Hazard QA Test, Case 20
=================================

============== ====================
checksum32     2_043_154_504       
date           2020-11-02T09:37:20 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 4, num_rlzs = 12

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                1.0                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     106                                       
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

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
====== ================== ====================
grp_id gsim               rlzs                
====== ================== ====================
0      '[SadighEtAl1997]' [0, 1, 2, 3, 4, 5]  
1      '[SadighEtAl1997]' [0, 1, 2, 6, 7, 8]  
2      '[SadighEtAl1997]' [0, 3, 6, 9]        
3      '[SadighEtAl1997]' [1, 4, 7, 10]       
4      '[SadighEtAl1997]' [2, 5, 8, 11]       
5      '[SadighEtAl1997]' [3, 4, 5, 9, 10, 11]
6      '[SadighEtAl1997]' [6, 7, 8, 9, 10, 11]
====== ================== ====================

Required parameters per tectonic region type
--------------------------------------------
===== ================== ========= ========== ==========
et_id gsims              distances siteparams ruptparams
===== ================== ========= ========== ==========
0     '[SadighEtAl1997]' rrup      vs30       mag rake  
1     '[SadighEtAl1997]' rrup      vs30       mag rake  
2     '[SadighEtAl1997]' rrup      vs30       mag rake  
3     '[SadighEtAl1997]' rrup      vs30       mag rake  
4     '[SadighEtAl1997]' rrup      vs30       mag rake  
5     '[SadighEtAl1997]' rrup      vs30       mag rake  
6     '[SadighEtAl1997]' rrup      vs30       mag rake  
7     '[SadighEtAl1997]' rrup      vs30       mag rake  
8     '[SadighEtAl1997]' rrup      vs30       mag rake  
9     '[SadighEtAl1997]' rrup      vs30       mag rake  
10    '[SadighEtAl1997]' rrup      vs30       mag rake  
11    '[SadighEtAl1997]' rrup      vs30       mag rake  
===== ================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
SFLT1;0   S    0.00260   1         56          
SFLT1;1   S    0.00257   1         58          
COMFLT1;1 C    0.00226   1         62          
COMFLT1;0 C    0.00225   1         29          
CHAR1;2   X    2.725E-04 1         1           
CHAR1;0   X    1.612E-04 1         1           
CHAR1;1   X    1.566E-04 1         1           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.00451  
S    0.00517  
X    5.903E-04
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       7      0.00195 56%    6.144E-04 0.00311
read_source_model  1      0.01625 nan    0.01625   0.01625
================== ====== ======= ====== ========= =======

Data transfer
-------------
================= =============================== ========
task              sent                            received
read_source_model                                 10.87 KB
preclassical      srcs=25.95 KB srcfilter=6.31 KB 1.68 KB 
================= =============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47357, maxmem=1.3 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.30110  0.0       1     
composite source model    0.29541  0.0       1     
total read_source_model   0.01625  0.0       1     
total preclassical        0.01366  0.41016   7     
========================= ======== ========= ======