Classical PSHA with source specific logic tree (3**2 realizations)
==================================================================

============== ===================
checksum32     283,798,826        
date           2019-10-01T06:08:39
engine_version 3.8.0-gite0871b5c35
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
2         16     S    310          0.01327   1.00000   310          23,370 
2         4      S    310          0.01205   1.00000   310          25,719 
2         10     S    310          0.00970   1.00000   310          31,966 
2         2      S    310          0.00934   1.00000   310          33,196 
2         12     S    310          0.00485   1.00000   310          63,931 
2         0      S    310          0.00403   1.00000   310          76,960 
2         8      S    310          0.00385   1.00000   310          80,570 
1         7      A    1,040        0.00380   1.00000   1,040        273,416
1         11     A    1,040        0.00342   1.00000   1,040        304,380
1         5      A    1,040        0.00281   1.00000   1,040        370,138
2         6      S    310          0.00263   1.00000   310          117,818
2         14     S    310          0.00194   1.00000   310          159,518
1         3      A    1,040        0.00185   1.00000   1,040        563,139
1         9      A    1,040        0.00171   1.00000   1,040        609,143
1         1      A    1,040        0.00157   1.00000   1,040        661,121
1         15     A    1,040        0.00121   1.00000   1,040        860,710
1         13     A    1,040        0.00114   1.00000   1,040        915,825
1         17     A    1,040        0.00109   1.00000   1,040        958,066
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.01859   9     
S    0.06165   9     
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 6 duplicate sources with multiplicity 3.0: ['1' '1' '1' '2' '2' '2']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.06784 0.01208 0.04046 0.08081 9      
preclassical       0.00717 0.00899 0.00145 0.02858 12     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ============================================== ========
task         sent                                           received
SourceReader apply_unc=14.19 KB ltmodel=1.76 KB fname=873 B 46.36 KB
preclassical srcs=23.21 KB params=7.12 KB srcfilter=2.61 KB 4.29 KB 
============ ============================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_23163             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.61057  0.0       9     
composite source model 0.21761  0.0       1     
total preclassical     0.08605  0.0       12    
store source_info      0.00678  0.0       1     
aggregate curves       0.00378  0.0       12    
====================== ======== ========= ======