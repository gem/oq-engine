Classical PSHA with source specific logic tree (3**2 realizations)
==================================================================

============== ===================
checksum32     3,958,530,442      
date           2019-10-23T16:26:41
engine_version 3.8.0-git2e0d8e6795
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
0      0.00323   310          310         
1      9.615E-04 1,040        1,040       
2      0.00323   310          310         
3      9.615E-04 1,040        1,040       
4      0.00323   310          310         
5      9.615E-04 1,040        1,040       
6      0.00323   310          310         
7      9.615E-04 1,040        1,040       
8      0.00323   310          310         
9      9.615E-04 1,040        1,040       
10     0.00323   310          310         
11     9.615E-04 1,040        1,040       
12     0.00323   310          310         
13     9.615E-04 1,040        1,040       
14     0.00323   310          310         
15     9.615E-04 1,040        1,040       
16     0.00323   310          310         
17     9.615E-04 1,040        1,040       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
2         12     S    310          0.00284   0.00323   310         
2         0      S    310          0.00262   0.00323   310         
2         8      S    310          0.00256   0.00323   310         
2         2      S    310          0.00256   0.00323   310         
2         4      S    310          0.00252   0.00323   310         
2         14     S    310          0.00250   0.00323   310         
2         10     S    310          0.00250   0.00323   310         
2         16     S    310          0.00220   0.00323   310         
2         6      S    310          0.00220   0.00323   310         
1         11     A    1,040        0.00122   9.615E-04 1,040       
1         13     A    1,040        0.00118   9.615E-04 1,040       
1         17     A    1,040        0.00116   9.615E-04 1,040       
1         9      A    1,040        0.00115   9.615E-04 1,040       
1         1      A    1,040        0.00105   9.615E-04 1,040       
1         15     A    1,040        9.782E-04 9.615E-04 1,040       
1         5      A    1,040        9.680E-04 9.615E-04 1,040       
1         7      A    1,040        9.596E-04 9.615E-04 1,040       
1         3      A    1,040        9.594E-04 9.615E-04 1,040       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00963  
S    0.02250  
==== =========

Duplicated sources
------------------
Found 0 unique sources and 6 duplicate sources with multiplicity 3.0: ['1' '1' '1' '2' '2' '2']

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.08160 0.02442   0.03668 0.11116 9      
preclassical       0.00203 7.590E-04 0.00118 0.00307 18     
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =============================================== ========
task         sent                                            received
SourceReader apply_unc=14.38 KB ltmodel=1.76 KB fname=936 B  49.32 KB
preclassical srcs=27.56 KB params=11.41 KB srcfilter=3.92 KB 6.01 KB 
============ =============================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_44542             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.73440  0.0       9     
composite source model 0.17181  0.0       1     
total preclassical     0.03652  0.0       18    
aggregate curves       0.00418  0.0       18    
store source_info      0.00232  0.0       1     
====================== ======== ========= ======