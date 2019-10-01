Classical PSHA with source specific logic tree (3**2 realizations)
==================================================================

============== ===================
checksum32     283,798,826        
date           2019-10-01T07:01:13
engine_version 3.8.0-gitbd71c2f960
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
2         10     S    310          0.00795   1.00000   310          39,018 
2         12     S    310          0.00464   1.00000   310          66,850 
2         8      S    310          0.00443   1.00000   310          70,026 
2         2      S    310          0.00430   1.00000   310          72,087 
2         16     S    310          0.00429   1.00000   310          72,320 
2         14     S    310          0.00415   1.00000   310          74,675 
2         6      S    310          0.00408   1.00000   310          75,926 
2         4      S    310          0.00375   1.00000   310          82,660 
2         0      S    310          0.00258   1.00000   310          120,170
1         9      A    1,040        0.00207   1.00000   1,040        501,215
1         11     A    1,040        0.00204   1.00000   1,040        509,172
1         5      A    1,040        0.00200   1.00000   1,040        519,790
1         17     A    1,040        0.00195   1.00000   1,040        533,457
1         13     A    1,040        0.00193   1.00000   1,040        538,196
1         1      A    1,040        0.00182   1.00000   1,040        570,803
1         7      A    1,040        0.00155   1.00000   1,040        670,676
1         15     A    1,040        0.00146   1.00000   1,040        711,131
1         3      A    1,040        0.00134   1.00000   1,040        778,108
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.01617   9     
S    0.04016   9     
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 6 duplicate sources with multiplicity 3.0: ['1' '1' '1' '2' '2' '2']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.04639 0.00305 0.04234 0.05027 9      
preclassical       0.00355 0.00170 0.00166 0.00833 18     
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
calc_6641              time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.41752  0.0       9     
composite source model 0.08300  0.0       1     
total preclassical     0.06385  0.0       18    
aggregate curves       0.00525  0.0       18    
store source_info      0.00278  0.0       1     
====================== ======== ========= ======