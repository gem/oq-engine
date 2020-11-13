Classical PSHA with non-trivial logic tree (1 source model + 5 (a, b) pairs per source + 3 Mmax per source
==========================================================================================================

============== ====================
checksum32     53_665_629          
date           2020-11-02T09:37:05 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 3, num_rlzs = 10

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    10                                        
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                0.1                                       
area_source_discretization      20.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     23                                        
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ===================== ============
grp_id gsim                  rlzs        
====== ===================== ============
0      '[BooreAtkinson2008]' [0]         
1      '[BooreAtkinson2008]' [0, 2]      
2      '[BooreAtkinson2008]' [0, 3, 6, 9]
3      '[BooreAtkinson2008]' [0, 5]      
4      '[BooreAtkinson2008]' [1]         
5      '[BooreAtkinson2008]' [1, 3, 7, 9]
6      '[BooreAtkinson2008]' [1, 7]      
7      '[BooreAtkinson2008]' [2]         
8      '[BooreAtkinson2008]' [2, 8]      
9      '[BooreAtkinson2008]' [3]         
10     '[BooreAtkinson2008]' [3, 4]      
11     '[BooreAtkinson2008]' [3, 7]      
12     '[BooreAtkinson2008]' [4]         
13     '[BooreAtkinson2008]' [4, 6]      
14     '[BooreAtkinson2008]' [5]         
15     '[BooreAtkinson2008]' [5, 6, 7]   
16     '[BooreAtkinson2008]' [5, 7, 9]   
17     '[BooreAtkinson2008]' [6]         
18     '[BooreAtkinson2008]' [8]         
19     '[BooreAtkinson2008]' [9]         
====== ===================== ============

Required parameters per tectonic region type
--------------------------------------------
===== ===================== ========= ========== ==========
et_id gsims                 distances siteparams ruptparams
===== ===================== ========= ========== ==========
0     '[BooreAtkinson2008]' rjb       vs30       mag rake  
1     '[BooreAtkinson2008]' rjb       vs30       mag rake  
2     '[BooreAtkinson2008]' rjb       vs30       mag rake  
3     '[BooreAtkinson2008]' rjb       vs30       mag rake  
4     '[BooreAtkinson2008]' rjb       vs30       mag rake  
5     '[BooreAtkinson2008]' rjb       vs30       mag rake  
6     '[BooreAtkinson2008]' rjb       vs30       mag rake  
7     '[BooreAtkinson2008]' rjb       vs30       mag rake  
8     '[BooreAtkinson2008]' rjb       vs30       mag rake  
9     '[BooreAtkinson2008]' rjb       vs30       mag rake  
===== ===================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
2;1       A    1.442E-04 1         90          
1;0       A    1.433E-04 1         68          
1;3       A    1.416E-04 1         60          
1;5       A    1.366E-04 1         60          
3;1       A    1.333E-04 1         90          
3;2       A    1.302E-04 1         102         
5;5       A    1.299E-04 1         52          
3;4       A    1.297E-04 1         90          
2;0       A    1.252E-04 1         90          
2;4       A    1.245E-04 1         78          
4;5       A    1.075E-04 1         60          
1;2       A    8.059E-05 1         60          
5;1       A    7.939E-05 1         60          
3;6       A    7.868E-05 1         78          
3;5       A    7.486E-05 1         78          
3;0       A    7.367E-05 1         102         
5;2       A    7.343E-05 1         60          
2;5       A    7.343E-05 1         102         
4;2       A    7.272E-05 1         52          
4;3       A    7.224E-05 1         52          
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00299  
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       11     7.978E-04 6%     7.048E-04 8.898E-04
read_source_model  1      0.00691   nan    0.00691   0.00691  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ================================ ========
task              sent                             received
read_source_model                                  3.47 KB 
preclassical      srcs=41.46 KB srcfilter=13.83 KB 3.52 KB 
================= ================================ ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47346, maxmem=1.5 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.27006  0.0       1     
composite source model    0.24766  0.0       1     
total preclassical        0.00878  0.37109   11    
total read_source_model   0.00691  0.0       1     
========================= ======== ========= ======