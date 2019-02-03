Classical Hazard QA Test, Case 21
=================================

============== ===================
checksum32     2,852,175,627      
date           2019-02-03T09:39:32
engine_version 3.4.0-gite8c42e513a
============== ===================

num_sites = 1, num_levels = 4

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
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
2      SadighEtAl1997() rrup      vs30       mag rake  
3      SadighEtAl1997() rrup      vs30       mag rake  
4      SadighEtAl1997() rrup      vs30       mag rake  
5      SadighEtAl1997() rrup      vs30       mag rake  
6      SadighEtAl1997() rrup      vs30       mag rake  
7      SadighEtAl1997() rrup      vs30       mag rake  
8      SadighEtAl1997() rrup      vs30       mag rake  
9      SadighEtAl1997() rrup      vs30       mag rake  
10     SadighEtAl1997() rrup      vs30       mag rake  
11     SadighEtAl1997() rrup      vs30       mag rake  
12     SadighEtAl1997() rrup      vs30       mag rake  
13     SadighEtAl1997() rrup      vs30       mag rake  
14     SadighEtAl1997() rrup      vs30       mag rake  
15     SadighEtAl1997() rrup      vs30       mag rake  
16     SadighEtAl1997() rrup      vs30       mag rake  
17     SadighEtAl1997() rrup      vs30       mag rake  
18     SadighEtAl1997() rrup      vs30       mag rake  
19     SadighEtAl1997() rrup      vs30       mag rake  
20     SadighEtAl1997() rrup      vs30       mag rake  
21     SadighEtAl1997() rrup      vs30       mag rake  
22     SadighEtAl1997() rrup      vs30       mag rake  
23     SadighEtAl1997() rrup      vs30       mag rake  
24     SadighEtAl1997() rrup      vs30       mag rake  
25     SadighEtAl1997() rrup      vs30       mag rake  
26     SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=27, rlzs=27)
  0,SadighEtAl1997(): [0]
  1,SadighEtAl1997(): [1]
  2,SadighEtAl1997(): [2]
  3,SadighEtAl1997(): [3]
  4,SadighEtAl1997(): [4]
  5,SadighEtAl1997(): [5]
  6,SadighEtAl1997(): [6]
  7,SadighEtAl1997(): [7]
  8,SadighEtAl1997(): [8]
  9,SadighEtAl1997(): [9]
  10,SadighEtAl1997(): [10]
  11,SadighEtAl1997(): [11]
  12,SadighEtAl1997(): [12]
  13,SadighEtAl1997(): [13]
  14,SadighEtAl1997(): [14]
  15,SadighEtAl1997(): [15]
  16,SadighEtAl1997(): [16]
  17,SadighEtAl1997(): [17]
  18,SadighEtAl1997(): [18]
  19,SadighEtAl1997(): [19]
  20,SadighEtAl1997(): [20]
  21,SadighEtAl1997(): [21]
  22,SadighEtAl1997(): [22]
  23,SadighEtAl1997(): [23]
  24,SadighEtAl1997(): [24]
  25,SadighEtAl1997(): [25]
  26,SadighEtAl1997(): [26]>

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
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
26     SFLT2     S    106   108   89           0.0       3.195E-05  2.00000   2         89    
26     SFLT1     S    104   106   132          0.0       1.502E-05  1.00000   1         132   
25     SFLT2     S    102   104   148          0.0       3.386E-05  2.00000   2         148   
25     SFLT1     S    100   102   132          0.0       4.292E-06  1.00000   1         132   
24     SFLT2     S    98    100   384          0.0       3.433E-05  2.00000   2         384   
24     SFLT1     S    96    98    132          0.0       4.292E-06  1.00000   1         132   
23     SFLT2     S    94    96    89           0.0       3.433E-05  2.00000   2         89    
23     SFLT1     S    92    94    198          0.0       4.530E-06  1.00000   1         198   
22     SFLT2     S    90    92    148          0.0       8.059E-05  2.00000   2         148   
22     SFLT1     S    88    90    198          0.0       4.530E-06  1.00000   1         198   
21     SFLT2     S    86    88    384          0.0       3.576E-05  2.00000   2         384   
21     SFLT1     S    84    86    198          0.0       4.530E-06  1.00000   1         198   
20     SFLT2     S    82    84    89           0.0       3.481E-05  2.00000   2         89    
20     SFLT1     S    80    82    99           0.0       4.768E-06  1.00000   1         99    
19     SFLT2     S    78    80    148          0.0       3.481E-05  2.00000   2         148   
19     SFLT1     S    76    78    99           0.0       4.530E-06  1.00000   1         99    
18     SFLT2     S    74    76    384          0.0       3.624E-05  2.00000   2         384   
18     SFLT1     S    72    74    99           0.0       4.292E-06  1.00000   1         99    
17     SFLT2     S    70    72    89           0.0       3.481E-05  2.00000   2         89    
17     SFLT1     S    68    70    27           0.0       4.530E-06  1.00000   1         27    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.0       54    
==== ========= ======

Duplicated sources
------------------
Found 2 source(s) with the same ID and 0 true duplicate(s)
Here is a fake duplicate: SFLT2

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.03340 0.00758 0.01906 0.06503 27     
split_filter       0.08582 NaN     0.08582 0.08582 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ======================================= ========
task               sent                                    received
read_source_models converter=8.25 KB fnames=2.82 KB        49.89 KB
split_filter       srcs=17.02 KB srcfilter=253 B seed=14 B 24.79 KB
================== ======================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.90182  0.38672   27    
total split_filter       0.08582  1.45703   1     
======================== ======== ========= ======