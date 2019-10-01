Classical PSHA with source specific logic tree (3**2 realizations)
==================================================================

============== ===================
checksum32     283,798,826        
date           2019-10-01T06:32:42
engine_version 3.8.0-git66affb82eb
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
=========== ======= =============== ================
smlt_path   weight  gsim_logic_tree num_realizations
=========== ======= =============== ================
b11_b21_b31 0.11089 trivial(1,1)    1               
b11_b21_b32 0.11089 trivial(1,1)    1               
b11_b21_b33 0.11122 trivial(1,1)    1               
b11_b22_b31 0.11089 trivial(1,1)    1               
b11_b22_b32 0.11089 trivial(1,1)    1               
b11_b22_b33 0.11122 trivial(1,1)    1               
b11_b23_b31 0.11122 trivial(1,1)    1               
b11_b23_b32 0.11122 trivial(1,1)    1               
b11_b23_b33 0.11156 trivial(1,1)    1               
=========== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
1      '[ToroEtAl2002]'      rjb                  mag       
2      '[BooreAtkinson2008]' rjb       vs30       mag rake  
3      '[ToroEtAl2002]'      rjb                  mag       
4      '[BooreAtkinson2008]' rjb       vs30       mag rake  
5      '[ToroEtAl2002]'      rjb                  mag       
6      '[BooreAtkinson2008]' rjb       vs30       mag rake  
7      '[ToroEtAl2002]'      rjb                  mag       
8      '[BooreAtkinson2008]' rjb       vs30       mag rake  
9      '[ToroEtAl2002]'      rjb                  mag       
10     '[BooreAtkinson2008]' rjb       vs30       mag rake  
11     '[ToroEtAl2002]'      rjb                  mag       
12     '[BooreAtkinson2008]' rjb       vs30       mag rake  
13     '[ToroEtAl2002]'      rjb                  mag       
14     '[BooreAtkinson2008]' rjb       vs30       mag rake  
15     '[ToroEtAl2002]'      rjb                  mag       
16     '[BooreAtkinson2008]' rjb       vs30       mag rake  
17     '[ToroEtAl2002]'      rjb                  mag       
====== ===================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=18, rlzs=9)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   310          310         
1      1.00000   1,040        1,040       
2      1.00000   310          310         
3      1.00000   1,040        1,040       
4      1.00000   310          310         
5      1.00000   1,040        1,040       
6      1.00000   310          310         
7      1.00000   1,040        1,040       
8      1.00000   310          310         
9      1.00000   1,040        1,040       
10     1.00000   310          310         
11     1.00000   1,040        1,040       
12     1.00000   310          310         
13     1.00000   1,040        1,040       
14     1.00000   310          310         
15     1.00000   1,040        1,040       
16     1.00000   310          310         
17     1.00000   1,040        1,040       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
2         10     S    310          0.00587   1.00000   310          52,812 
2         16     S    310          0.00434   1.00000   310          71,371 
2         14     S    310          0.00422   1.00000   310          73,426 
2         4      S    310          0.00419   1.00000   310          74,012 
2         0      S    310          0.00418   1.00000   310          74,227 
2         12     S    310          0.00383   1.00000   310          81,022 
2         8      S    310          0.00313   1.00000   310          99,126 
2         6      S    310          0.00308   1.00000   310          100,739
2         2      S    310          0.00299   1.00000   310          103,819
1         7      A    1,040        0.00212   1.00000   1,040        491,612
1         17     A    1,040        0.00207   1.00000   1,040        501,215
1         11     A    1,040        0.00204   1.00000   1,040        510,005
1         3      A    1,040        0.00195   1.00000   1,040        533,457
1         9      A    1,040        0.00193   1.00000   1,040        539,127
1         13     A    1,040        0.00193   1.00000   1,040        539,861
1         15     A    1,040        0.00189   1.00000   1,040        549,588
1         5      A    1,040        0.00180   1.00000   1,040        576,918
1         1      A    1,040        0.00175   1.00000   1,040        595,018
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.01748   9     
S    0.03582   9     
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 6 duplicate sources with multiplicity 3.0: ['1' '1' '1' '2' '2' '2']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.04388 0.00179 0.04176 0.04593 9      
preclassical       0.00339 0.00121 0.00216 0.00639 18     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ============================================== ========
task         sent                                           received
SourceReader apply_unc=14.38 KB ltmodel=1.76 KB fname=936 B 46.42 KB
preclassical srcs=27.56 KB params=10.69 KB srcfilter=3.9 KB 6.01 KB 
============ ============================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_6486              time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.39488  0.0       9     
composite source model 0.08785  0.0       1     
total preclassical     0.06103  0.0       18    
aggregate curves       0.00441  0.0       18    
store source_info      0.00207  0.0       1     
====================== ======== ========= ======