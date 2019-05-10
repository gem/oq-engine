Classical PSHA with source specific logic tree (3**2 realizations)
==================================================================

============== ===================
checksum32     283,798,826        
date           2019-05-10T05:07:56
engine_version 3.5.0-gitbaeb4c1e35
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

  <RlzsAssoc(size=18, rlzs=9)
  0,'[BooreAtkinson2008]': [0]
  1,'[ToroEtAl2002]': [0]
  2,'[BooreAtkinson2008]': [1]
  3,'[ToroEtAl2002]': [1]
  4,'[BooreAtkinson2008]': [2]
  5,'[ToroEtAl2002]': [2]
  6,'[BooreAtkinson2008]': [3]
  7,'[ToroEtAl2002]': [3]
  8,'[BooreAtkinson2008]': [4]
  9,'[ToroEtAl2002]': [4]
  10,'[BooreAtkinson2008]': [5]
  11,'[ToroEtAl2002]': [5]
  12,'[BooreAtkinson2008]': [6]
  13,'[ToroEtAl2002]': [6]
  14,'[BooreAtkinson2008]': [7]
  15,'[ToroEtAl2002]': [7]
  16,'[BooreAtkinson2008]': [8]
  17,'[ToroEtAl2002]': [8]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ======================== ============ ============
source_model     grp_id trt                      eff_ruptures tot_ruptures
================ ====== ======================== ============ ============
source_model.xml 0      Active Shallow Crust     310          310         
source_model.xml 1      Stable Continental Crust 1,040        1,040       
source_model.xml 2      Active Shallow Crust     310          310         
source_model.xml 3      Stable Continental Crust 1,040        1,040       
source_model.xml 4      Active Shallow Crust     310          310         
source_model.xml 5      Stable Continental Crust 1,040        1,040       
source_model.xml 6      Active Shallow Crust     310          310         
source_model.xml 7      Stable Continental Crust 1,040        1,040       
source_model.xml 8      Active Shallow Crust     310          310         
source_model.xml 9      Stable Continental Crust 1,040        1,040       
source_model.xml 10     Active Shallow Crust     310          310         
source_model.xml 11     Stable Continental Crust 1,040        1,040       
source_model.xml 12     Active Shallow Crust     310          310         
source_model.xml 13     Stable Continental Crust 1,040        1,040       
source_model.xml 14     Active Shallow Crust     310          310         
source_model.xml 15     Stable Continental Crust 1,040        1,040       
source_model.xml 16     Active Shallow Crust     310          310         
source_model.xml 17     Stable Continental Crust 1,040        1,040       
================ ====== ======================== ============ ============

============= ======
#TRT models   18    
#eff_ruptures 12,150
#tot_ruptures 12,150
#tot_weight   3,726 
============= ======

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
10     2         S    35    38    310          0.00635   1.00000   310   
0      2         S    0     3     310          0.00574   1.00000   310   
6      2         S    21    24    310          0.00539   1.00000   310   
8      2         S    28    31    310          0.00521   1.00000   310   
4      2         S    14    17    310          0.00511   1.00000   310   
16     2         S    56    59    310          0.00494   1.00000   310   
2      2         S    7     10    310          0.00472   1.00000   310   
14     2         S    49    52    310          0.00461   1.00000   310   
12     2         S    42    45    310          0.00441   1.00000   310   
1      1         A    3     7     1,040        0.00287   1.00000   104   
13     1         A    45    49    1,040        0.00285   1.00000   104   
7      1         A    24    28    1,040        0.00282   1.00000   104   
9      1         A    31    35    1,040        0.00263   1.00000   104   
17     1         A    59    63    1,040        0.00246   1.00000   104   
5      1         A    17    21    1,040        0.00230   1.00000   104   
15     1         A    52    56    1,040        0.00168   1.00000   104   
3      1         A    10    14    1,040        0.00160   1.00000   104   
11     1         A    38    42    1,040        0.00156   1.00000   104   
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.02077   9     
S    0.04647   9     
==== ========= ======

Duplicated sources
------------------
['1', '2']
Found 2 source(s) with the same ID and 2 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.02334 0.00211 0.01875 0.02529 9      
preclassical       0.00455 0.00239 0.00185 0.01168 18     
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ========================================================== ========
task               sent                                                       received
read_source_models converter=2.75 KB fnames=963 B                             28.02 KB
preclassical       srcs=27.46 KB params=10 KB srcfilter=3.85 KB gsims=2.65 KB 6.05 KB 
================== ========================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.21006  0.0       9     
total preclassical       0.08187  0.0       18    
managing sources         0.00762  0.0       1     
aggregate curves         0.00219  0.0       18    
store source_info        0.00154  0.0       1     
======================== ======== ========= ======