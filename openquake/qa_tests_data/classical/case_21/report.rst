Classical Hazard QA Test, Case 21
=================================

============== ===================
checksum32     124,630,436        
date           2018-06-26T14:57:29
engine_version 3.2.0-gitb0cd949   
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
SFLT2     SimpleFaultSource 89           0.16200   1.884E-05  1.00000   61        0     
SFLT1     SimpleFaultSource 132          0.08860   2.861E-06  1.00000   32        0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.25060   2     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00748 0.00364 0.00257 0.01876 41       
count_eff_ruptures 0.00514 0.00219 0.00220 0.01021 65       
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=63, weight=58, duration=0 s, sources="SFLT2"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   58      NaN    58  58  1
======== ======= ====== === === =

Slowest task
------------
taskno=27, weight=83, duration=0 s, sources="SFLT1 SFLT2"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 0.0    1   1   2
weight   41      23     25  58  2
======== ======= ====== === === =

Data transfer
-------------
================== ================================================================================= ========
task               sent                                                                              received
RtreeFilter        srcs=55.52 KB monitor=12.89 KB srcfilter=11.17 KB                                 61.48 KB
count_eff_ruptures sources=83.28 KB param=27.87 KB monitor=20.88 KB srcfilter=15.62 KB gsims=7.62 KB 23.51 KB
================== ================================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.63428   0.0       1     
total count_eff_ruptures       0.33386   6.50391   65    
total prefilter                0.30656   4.23828   41    
managing sources               0.30462   0.0       1     
aggregate curves               0.02380   0.0       65    
unpickling prefilter           0.01666   0.0       41    
unpickling count_eff_ruptures  0.01623   0.0       65    
store source_info              0.00966   0.0       1     
splitting sources              0.00123   0.0       1     
reading site collection        3.638E-04 0.0       1     
============================== ========= ========= ======