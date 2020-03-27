Classical PSHA with source specific logic tree (3**2 realizations)
==================================================================

============== ===================
checksum32     3_958_530_442      
date           2020-03-13T11:22:54
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 14, num_rlzs = 9

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

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
=========== ======= ================
smlt_path   weight  num_realizations
=========== ======= ================
b11_b21_b31 0.11089 1               
b11_b21_b32 0.11089 1               
b11_b21_b33 0.11122 1               
b11_b22_b31 0.11089 1               
b11_b22_b32 0.11089 1               
b11_b22_b33 0.11122 1               
b11_b23_b31 0.11122 1               
b11_b23_b32 0.11122 1               
b11_b23_b33 0.11156 1               
=========== ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
1      '[BooreAtkinson2008]' rjb       vs30       mag rake  
2      '[BooreAtkinson2008]' rjb       vs30       mag rake  
3      '[BooreAtkinson2008]' rjb       vs30       mag rake  
4      '[BooreAtkinson2008]' rjb       vs30       mag rake  
5      '[BooreAtkinson2008]' rjb       vs30       mag rake  
6      '[BooreAtkinson2008]' rjb       vs30       mag rake  
7      '[BooreAtkinson2008]' rjb       vs30       mag rake  
8      '[BooreAtkinson2008]' rjb       vs30       mag rake  
9      '[ToroEtAl2002]'      rjb                  mag       
10     '[ToroEtAl2002]'      rjb                  mag       
11     '[ToroEtAl2002]'      rjb                  mag       
12     '[ToroEtAl2002]'      rjb                  mag       
13     '[ToroEtAl2002]'      rjb                  mag       
14     '[ToroEtAl2002]'      rjb                  mag       
15     '[ToroEtAl2002]'      rjb                  mag       
16     '[ToroEtAl2002]'      rjb                  mag       
17     '[ToroEtAl2002]'      rjb                  mag       
====== ===================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.03226   310          310         
1      0.03226   310          310         
2      0.03226   310          310         
9      0.05000   1_040        1_040       
12     0.05000   1_040        1_040       
15     0.05000   1_040        1_040       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
2         0      S    310          0.02201   0.03226   310         
2         1      S    310          0.02172   0.03226   310         
2         2      S    310          0.02157   0.03226   310         
1         12     A    1_040        0.00741   0.05000   1_040       
1         9      A    1_040        0.00723   0.05000   1_040       
1         15     A    1_040        0.00676   0.05000   1_040       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.02140  
S    0.06530  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.02535 0.00350 0.02257 0.03024 6      
read_source_model  0.01763 NaN     0.01763 0.01763 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ============================================== ========
task              sent                                           received
read_source_model                                                3.04 KB 
preclassical      srcs=10.13 KB params=4.27 KB srcfilter=1.31 KB 2.23 KB 
================= ============================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66997                  time_sec memory_mb counts
=========================== ======== ========= ======
composite source model      0.17608  0.0       1     
total preclassical          0.15212  0.0       6     
splitting/filtering sources 0.05981  0.0       6     
total read_source_model     0.01763  0.0       1     
store source_info           0.00270  0.0       1     
aggregate curves            0.00175  0.0       6     
=========================== ======== ========= ======