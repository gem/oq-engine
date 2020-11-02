Classical Hazard QA Test, Case 21
=================================

============== ====================
checksum32     951_606_355         
date           2020-11-02T09:37:00 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 4, num_rlzs = 27

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
====== ================== =================================
grp_id gsim               rlzs                             
====== ================== =================================
0      '[SadighEtAl1997]' [0, 1, 2]                        
1      '[SadighEtAl1997]' [0, 3, 6, 9, 12, 15, 18, 21, 24] 
2      '[SadighEtAl1997]' [1, 4, 7, 10, 13, 16, 19, 22, 25]
3      '[SadighEtAl1997]' [2, 5, 8, 11, 14, 17, 20, 23, 26]
4      '[SadighEtAl1997]' [3, 4, 5]                        
5      '[SadighEtAl1997]' [6, 7, 8]                        
6      '[SadighEtAl1997]' [9, 10, 11]                      
7      '[SadighEtAl1997]' [12, 13, 14]                     
8      '[SadighEtAl1997]' [15, 16, 17]                     
9      '[SadighEtAl1997]' [18, 19, 20]                     
10     '[SadighEtAl1997]' [21, 22, 23]                     
11     '[SadighEtAl1997]' [24, 25, 26]                     
====== ================== =================================

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
12    '[SadighEtAl1997]' rrup      vs30       mag rake  
13    '[SadighEtAl1997]' rrup      vs30       mag rake  
14    '[SadighEtAl1997]' rrup      vs30       mag rake  
15    '[SadighEtAl1997]' rrup      vs30       mag rake  
16    '[SadighEtAl1997]' rrup      vs30       mag rake  
17    '[SadighEtAl1997]' rrup      vs30       mag rake  
18    '[SadighEtAl1997]' rrup      vs30       mag rake  
19    '[SadighEtAl1997]' rrup      vs30       mag rake  
20    '[SadighEtAl1997]' rrup      vs30       mag rake  
21    '[SadighEtAl1997]' rrup      vs30       mag rake  
22    '[SadighEtAl1997]' rrup      vs30       mag rake  
23    '[SadighEtAl1997]' rrup      vs30       mag rake  
24    '[SadighEtAl1997]' rrup      vs30       mag rake  
25    '[SadighEtAl1997]' rrup      vs30       mag rake  
26    '[SadighEtAl1997]' rrup      vs30       mag rake  
===== ================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
SFLT1;7   S    0.00202   1         132         
SFLT1;5   S    0.00195   1         25          
SFLT1;2   S    0.00189   1         60          
SFLT1;1   S    0.00185   1         90          
SFLT2;1   S    0.00183   1         148         
SFLT1;4   S    0.00181   1         27          
SFLT1;3   S    0.00181   1         81          
SFLT1;0   S    0.00180   1         150         
SFLT2;0   S    0.00180   1         384         
SFLT2;2   S    0.00179   1         89          
SFLT1;6   S    0.00173   1         198         
SFLT1;8   S    0.00164   1         99          
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.02192  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       12     0.00231 4%     0.00209 0.00255
read_source_model  1      0.00257 nan    0.00257 0.00257
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= ================================ ========
task              sent                             received
read_source_model                                  1.77 KB 
preclassical      srcs=14.77 KB srcfilter=11.12 KB 2.87 KB 
================= ================================ ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47340, maxmem=1.5 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.22109  0.0       1     
composite source model    0.21294  0.0       1     
total preclassical        0.02768  0.50781   12    
total read_source_model   0.00257  0.0       1     
========================= ======== ========= ======