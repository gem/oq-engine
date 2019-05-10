Classical Hazard QA Test, Case 21
=================================

============== ===================
checksum32     2,852,175,627      
date           2019-05-10T05:07:52
engine_version 3.5.0-gitbaeb4c1e35
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 27

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     106               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

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
====================== ======= =============== ================
smlt_path              weight  gsim_logic_tree num_realizations
====================== ======= =============== ================
b1_mfd1_high_dip_dip30 0.01320 trivial(1)      1               
b1_mfd1_high_dip_dip45 0.03960 trivial(1)      1               
b1_mfd1_high_dip_dip60 0.01320 trivial(1)      1               
b1_mfd1_low_dip_dip30  0.01320 trivial(1)      1               
b1_mfd1_low_dip_dip45  0.03960 trivial(1)      1               
b1_mfd1_low_dip_dip60  0.01320 trivial(1)      1               
b1_mfd1_mid_dip_dip30  0.03960 trivial(1)      1               
b1_mfd1_mid_dip_dip45  0.11880 trivial(1)      1               
b1_mfd1_mid_dip_dip60  0.03960 trivial(1)      1               
b1_mfd2_high_dip_dip30 0.01360 trivial(1)      1               
b1_mfd2_high_dip_dip45 0.04080 trivial(1)      1               
b1_mfd2_high_dip_dip60 0.01360 trivial(1)      1               
b1_mfd2_low_dip_dip30  0.01360 trivial(1)      1               
b1_mfd2_low_dip_dip45  0.04080 trivial(1)      1               
b1_mfd2_low_dip_dip60  0.01360 trivial(1)      1               
b1_mfd2_mid_dip_dip30  0.04080 trivial(1)      1               
b1_mfd2_mid_dip_dip45  0.12240 trivial(1)      1               
b1_mfd2_mid_dip_dip60  0.04080 trivial(1)      1               
b1_mfd3_high_dip_dip30 0.01320 trivial(1)      1               
b1_mfd3_high_dip_dip45 0.03960 trivial(1)      1               
b1_mfd3_high_dip_dip60 0.01320 trivial(1)      1               
b1_mfd3_low_dip_dip30  0.01320 trivial(1)      1               
b1_mfd3_low_dip_dip45  0.03960 trivial(1)      1               
b1_mfd3_low_dip_dip60  0.01320 trivial(1)      1               
b1_mfd3_mid_dip_dip30  0.03960 trivial(1)      1               
b1_mfd3_mid_dip_dip45  0.11880 trivial(1)      1               
b1_mfd3_mid_dip_dip60  0.03960 trivial(1)      1               
====================== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
2      '[SadighEtAl1997]' rrup      vs30       mag rake  
3      '[SadighEtAl1997]' rrup      vs30       mag rake  
4      '[SadighEtAl1997]' rrup      vs30       mag rake  
5      '[SadighEtAl1997]' rrup      vs30       mag rake  
6      '[SadighEtAl1997]' rrup      vs30       mag rake  
7      '[SadighEtAl1997]' rrup      vs30       mag rake  
8      '[SadighEtAl1997]' rrup      vs30       mag rake  
9      '[SadighEtAl1997]' rrup      vs30       mag rake  
10     '[SadighEtAl1997]' rrup      vs30       mag rake  
11     '[SadighEtAl1997]' rrup      vs30       mag rake  
12     '[SadighEtAl1997]' rrup      vs30       mag rake  
13     '[SadighEtAl1997]' rrup      vs30       mag rake  
14     '[SadighEtAl1997]' rrup      vs30       mag rake  
15     '[SadighEtAl1997]' rrup      vs30       mag rake  
16     '[SadighEtAl1997]' rrup      vs30       mag rake  
17     '[SadighEtAl1997]' rrup      vs30       mag rake  
18     '[SadighEtAl1997]' rrup      vs30       mag rake  
19     '[SadighEtAl1997]' rrup      vs30       mag rake  
20     '[SadighEtAl1997]' rrup      vs30       mag rake  
21     '[SadighEtAl1997]' rrup      vs30       mag rake  
22     '[SadighEtAl1997]' rrup      vs30       mag rake  
23     '[SadighEtAl1997]' rrup      vs30       mag rake  
24     '[SadighEtAl1997]' rrup      vs30       mag rake  
25     '[SadighEtAl1997]' rrup      vs30       mag rake  
26     '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=27, rlzs=27)
  0,'[SadighEtAl1997]': [0]
  1,'[SadighEtAl1997]': [1]
  2,'[SadighEtAl1997]': [2]
  3,'[SadighEtAl1997]': [3]
  4,'[SadighEtAl1997]': [4]
  5,'[SadighEtAl1997]': [5]
  6,'[SadighEtAl1997]': [6]
  7,'[SadighEtAl1997]': [7]
  8,'[SadighEtAl1997]': [8]
  9,'[SadighEtAl1997]': [9]
  10,'[SadighEtAl1997]': [10]
  11,'[SadighEtAl1997]': [11]
  12,'[SadighEtAl1997]': [12]
  13,'[SadighEtAl1997]': [13]
  14,'[SadighEtAl1997]': [14]
  15,'[SadighEtAl1997]': [15]
  16,'[SadighEtAl1997]': [16]
  17,'[SadighEtAl1997]': [17]
  18,'[SadighEtAl1997]': [18]
  19,'[SadighEtAl1997]': [19]
  20,'[SadighEtAl1997]': [20]
  21,'[SadighEtAl1997]': [21]
  22,'[SadighEtAl1997]': [22]
  23,'[SadighEtAl1997]': [23]
  24,'[SadighEtAl1997]': [24]
  25,'[SadighEtAl1997]': [25]
  26,'[SadighEtAl1997]': [26]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 444          296         
source_model.xml 1      Active Shallow Crust 208          296         
source_model.xml 2      Active Shallow Crust 149          296         
source_model.xml 3      Active Shallow Crust 534          296         
source_model.xml 4      Active Shallow Crust 298          296         
source_model.xml 5      Active Shallow Crust 239          296         
source_model.xml 6      Active Shallow Crust 474          296         
source_model.xml 7      Active Shallow Crust 238          296         
source_model.xml 8      Active Shallow Crust 179          296         
source_model.xml 9      Active Shallow Crust 409          296         
source_model.xml 10     Active Shallow Crust 173          296         
source_model.xml 11     Active Shallow Crust 114          296         
source_model.xml 12     Active Shallow Crust 465          296         
source_model.xml 13     Active Shallow Crust 229          296         
source_model.xml 14     Active Shallow Crust 170          296         
source_model.xml 15     Active Shallow Crust 411          296         
source_model.xml 16     Active Shallow Crust 175          296         
source_model.xml 17     Active Shallow Crust 116          296         
source_model.xml 18     Active Shallow Crust 483          296         
source_model.xml 19     Active Shallow Crust 247          296         
source_model.xml 20     Active Shallow Crust 188          296         
source_model.xml 21     Active Shallow Crust 582          296         
source_model.xml 22     Active Shallow Crust 346          296         
source_model.xml 23     Active Shallow Crust 287          296         
source_model.xml 24     Active Shallow Crust 516          296         
source_model.xml 25     Active Shallow Crust 280          296         
source_model.xml 26     Active Shallow Crust 221          296         
================ ====== ==================== ============ ============

============= =====
#TRT models   27   
#eff_ruptures 8,175
#tot_ruptures 7,992
#tot_weight   8,175
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
6      SFLT1     S    24    26    90           0.00803   1.00000   90    
3      SFLT2     S    14    16    384          0.00615   1.00000   384   
2      SFLT2     S    10    12    89           0.00582   1.00000   89    
4      SFLT1     S    16    18    150          0.00577   1.00000   150   
5      SFLT1     S    20    22    150          0.00576   1.00000   150   
0      SFLT2     S    2     4     384          0.00547   1.00000   384   
0      SFLT1     S    0     2     60           0.00544   1.00000   60    
6      SFLT2     S    26    28    384          0.00516   1.00000   384   
8      SFLT1     S    32    34    90           0.00452   1.00000   90    
1      SFLT1     S    4     6     60           0.00431   1.00000   60    
17     SFLT2     S    70    72    89           0.00402   1.00000   89    
10     SFLT1     S    40    42    25           0.00399   1.00000   25    
9      SFLT2     S    38    40    384          0.00389   1.00000   384   
13     SFLT1     S    52    54    81           0.00322   1.00000   81    
5      SFLT2     S    22    24    89           0.00295   1.00000   89    
21     SFLT2     S    86    88    384          0.00290   1.00000   384   
15     SFLT2     S    62    64    384          0.00284   1.00000   384   
3      SFLT1     S    12    14    150          0.00283   1.00000   150   
20     SFLT1     S    80    82    99           0.00276   1.00000   99    
21     SFLT1     S    84    86    198          0.00258   1.00000   198   
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.15163   54    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.02107 0.00566 0.01705 0.03985 27     
preclassical       0.00482 0.00221 0.00236 0.00925 34     
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================================= ========
task               sent                                                          received
read_source_models converter=8.25 KB fnames=2.82 KB                              49.89 KB
preclassical       srcs=43.44 KB params=16.17 KB srcfilter=7.27 KB gsims=4.88 KB 12.33 KB
================== ============================================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.56894  0.0       27    
total preclassical       0.16376  0.25391   34    
managing sources         0.00712  0.0       1     
aggregate curves         0.00507  0.0       34    
store source_info        0.00190  0.0       1     
======================== ======== ========= ======