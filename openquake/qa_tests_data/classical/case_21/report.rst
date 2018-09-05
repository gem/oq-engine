Classical Hazard QA Test, Case 21
=================================

============== ===================
checksum32     124,630,436        
date           2018-09-05T10:04:32
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 1, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
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
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====================== ======= =============== ================
smlt_path              weight  gsim_logic_tree num_realizations
====================== ======= =============== ================
b1_mfd1_high_dip_dip30 0.01320 trivial(1)      1/1             
b1_mfd1_high_dip_dip45 0.03960 trivial(1)      1/1             
b1_mfd1_high_dip_dip60 0.01320 trivial(1)      1/1             
b1_mfd1_low_dip_dip30  0.01320 trivial(1)      1/1             
b1_mfd1_low_dip_dip45  0.03960 trivial(1)      1/1             
b1_mfd1_low_dip_dip60  0.01320 trivial(1)      1/1             
b1_mfd1_mid_dip_dip30  0.03960 trivial(1)      1/1             
b1_mfd1_mid_dip_dip45  0.11880 trivial(1)      1/1             
b1_mfd1_mid_dip_dip60  0.03960 trivial(1)      1/1             
b1_mfd2_high_dip_dip30 0.01360 trivial(1)      1/1             
b1_mfd2_high_dip_dip45 0.04080 trivial(1)      1/1             
b1_mfd2_high_dip_dip60 0.01360 trivial(1)      1/1             
b1_mfd2_low_dip_dip30  0.01360 trivial(1)      1/1             
b1_mfd2_low_dip_dip45  0.04080 trivial(1)      1/1             
b1_mfd2_low_dip_dip60  0.01360 trivial(1)      1/1             
b1_mfd2_mid_dip_dip30  0.04080 trivial(1)      1/1             
b1_mfd2_mid_dip_dip45  0.12240 trivial(1)      1/1             
b1_mfd2_mid_dip_dip60  0.04080 trivial(1)      1/1             
b1_mfd3_high_dip_dip30 0.01320 trivial(1)      1/1             
b1_mfd3_high_dip_dip45 0.03960 trivial(1)      1/1             
b1_mfd3_high_dip_dip60 0.01320 trivial(1)      1/1             
b1_mfd3_low_dip_dip30  0.01320 trivial(1)      1/1             
b1_mfd3_low_dip_dip45  0.03960 trivial(1)      1/1             
b1_mfd3_low_dip_dip60  0.01320 trivial(1)      1/1             
b1_mfd3_mid_dip_dip30  0.03960 trivial(1)      1/1             
b1_mfd3_mid_dip_dip45  0.11880 trivial(1)      1/1             
b1_mfd3_mid_dip_dip60  0.03960 trivial(1)      1/1             
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
source_model.xml 1      Active Shallow Crust 268          296         
source_model.xml 2      Active Shallow Crust 207          296         
source_model.xml 3      Active Shallow Crust 534          296         
source_model.xml 4      Active Shallow Crust 298          296         
source_model.xml 5      Active Shallow Crust 239          296         
source_model.xml 6      Active Shallow Crust 474          296         
source_model.xml 7      Active Shallow Crust 238          296         
source_model.xml 8      Active Shallow Crust 204          296         
source_model.xml 9      Active Shallow Crust 498          296         
source_model.xml 10     Active Shallow Crust 198          296         
source_model.xml 11     Active Shallow Crust 172          296         
source_model.xml 12     Active Shallow Crust 465          296         
source_model.xml 13     Active Shallow Crust 229          296         
source_model.xml 14     Active Shallow Crust 197          296         
source_model.xml 15     Active Shallow Crust 500          296         
source_model.xml 16     Active Shallow Crust 202          296         
source_model.xml 17     Active Shallow Crust 174          296         
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
#eff_ruptures 8,691
#tot_ruptures 7,992
#tot_weight   8,175
============= =====

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
SFLT2     SimpleFaultSource 89           0.14695   1.836E-05  1.00000   61        0     
SFLT1     SimpleFaultSource 132          0.06808   2.384E-06  1.00000   32        0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.21504   2     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ======= ======= ======= =========
operation-duration   mean    stddev  min     max     num_tasks
pickle_source_models 0.01879 NaN     0.01879 0.01879 1        
count_eff_ruptures   0.00398 0.00189 0.00164 0.00993 65       
preprocess           0.00345 0.00189 0.00125 0.01183 68       
==================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=61, weight=132, duration=0 s, sources="SFLT1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   132     NaN    132 132 1
======== ======= ====== === === =

Slowest task
------------
taskno=9, weight=210, duration=0 s, sources="SFLT2"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   210     NaN    210 210 1
======== ======= ====== === === =

Data transfer
-------------
==================== ================================================================================ ========
task                 sent                                                                             received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                             156 B   
count_eff_ruptures   sources=83.4 KB param=32.63 KB monitor=19.49 KB srcfilter=13.96 KB gsims=7.62 KB 23.51 KB
preprocess           srcs=74.51 KB monitor=21.18 KB srcfilter=16.8 KB param=2.39 KB                   80.35 KB
==================== ================================================================================ ========

Slowest operations
------------------
========================== ======== ========= ======
operation                  time_sec memory_mb counts
========================== ======== ========= ======
total count_eff_ruptures   0.25842  4.67969   65    
managing sources           0.25779  0.0       1     
total preprocess           0.23433  0.87109   68    
total pickle_source_models 0.01879  0.0       1     
aggregate curves           0.01499  0.0       65    
store source_info          0.00710  0.0       1     
splitting sources          0.00143  0.0       1     
========================== ======== ========= ======