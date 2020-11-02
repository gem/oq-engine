Classical PSHA with non-trivial logic tree (1 source model + 5 (a, b) pairs per source + 3 Mmax per source
==========================================================================================================

============== ====================
checksum32     53_665_629          
date           2020-11-02T08:42:24 
engine_version 3.11.0-gitd13380ddb1
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
====== =================== ============
grp_id gsim                rlzs        
====== =================== ============
0      [BooreAtkinson2008] [0]         
1      [BooreAtkinson2008] [0, 2]      
2      [BooreAtkinson2008] [0, 3, 6, 9]
3      [BooreAtkinson2008] [0, 5]      
4      [BooreAtkinson2008] [1]         
5      [BooreAtkinson2008] [1, 3, 7, 9]
6      [BooreAtkinson2008] [1, 7]      
7      [BooreAtkinson2008] [2]         
8      [BooreAtkinson2008] [2, 8]      
9      [BooreAtkinson2008] [3]         
10     [BooreAtkinson2008] [3, 4]      
11     [BooreAtkinson2008] [3, 7]      
12     [BooreAtkinson2008] [4]         
13     [BooreAtkinson2008] [4, 6]      
14     [BooreAtkinson2008] [5]         
15     [BooreAtkinson2008] [5, 6, 7]   
16     [BooreAtkinson2008] [5, 7, 9]   
17     [BooreAtkinson2008] [6]         
18     [BooreAtkinson2008] [8]         
19     [BooreAtkinson2008] [9]         
====== =================== ============

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
1;0       A    1.397E-04 1         68          
3;4       A    1.366E-04 1         90          
3;1       A    1.307E-04 1         90          
3;2       A    1.299E-04 1         102         
1;5       A    1.299E-04 1         60          
2;1       A    1.280E-04 1         90          
2;4       A    1.264E-04 1         78          
5;5       A    1.256E-04 1         52          
1;3       A    1.256E-04 1         60          
2;0       A    1.254E-04 1         90          
4;5       A    1.137E-04 1         60          
2;5       A    9.346E-05 1         102         
4;2       A    7.820E-05 1         52          
4;3       A    7.677E-05 1         52          
1;2       A    7.463E-05 1         60          
3;3       A    7.415E-05 1         78          
5;2       A    7.367E-05 1         60          
5;1       A    7.296E-05 1         60          
1;4       A    7.153E-05 1         68          
5;0       A    7.105E-05 1         52          
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00295  
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       11     7.924E-04 5%     7.212E-04 8.862E-04
read_source_model  1      0.00667   nan    0.00667   0.00667  
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
calc_46632, maxmem=1.5 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.27234  0.0       1     
composite source model    0.26653  0.0       1     
total preclassical        0.00872  0.28125   11    
total read_source_model   0.00667  0.0       1     
========================= ======== ========= ======