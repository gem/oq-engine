Classical Hazard QA Test, Case 21
=================================

============== ===================
checksum32     124,630,436        
date           2018-12-13T12:57:48
engine_version 3.3.0-git68d7d11268
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
0      SFLT1     S    0     2     60           0.0       3.695E-05  0.0       1         0.0   
0      SFLT2     S    2     4     384          0.0       1.812E-04  0.0       2         0.0   
1      SFLT1     S    0     2     60           0.0       1.597E-05  0.0       1         0.0   
1      SFLT2     S    2     4     148          0.0       1.035E-04  0.0       2         0.0   
2      SFLT1     S    0     2     60           0.0       1.287E-05  0.0       1         0.0   
2      SFLT2     S    2     4     89           0.0       9.108E-05  0.0       2         0.0   
3      SFLT1     S    0     2     150          0.0       1.168E-05  0.0       1         0.0   
3      SFLT2     S    2     4     384          0.0       9.203E-05  0.0       2         0.0   
4      SFLT1     S    0     2     150          0.0       1.192E-05  0.0       1         0.0   
4      SFLT2     S    2     4     148          0.0       8.440E-05  0.0       2         0.0   
5      SFLT1     S    0     2     150          0.0       1.097E-05  0.0       1         0.0   
5      SFLT2     S    2     4     89           0.0       8.249E-05  0.0       2         0.0   
6      SFLT1     S    0     2     90           0.0       1.097E-05  0.0       1         0.0   
6      SFLT2     S    2     4     384          0.0       8.249E-05  0.0       2         0.0   
7      SFLT1     S    0     2     90           0.0       1.097E-05  0.0       1         0.0   
7      SFLT2     S    2     4     148          0.0       8.345E-05  0.0       2         0.0   
8      SFLT1     S    0     2     90           0.0       1.097E-05  0.0       1         0.0   
8      SFLT2     S    2     4     89           0.0       8.106E-05  0.0       2         0.0   
9      SFLT1     S    0     2     25           0.0       1.764E-05  0.0       1         0.0   
9      SFLT2     S    2     4     384          0.0       8.392E-05  0.0       2         0.0   
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
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.04190 0.01279 0.01803 0.08132 27     
split_filter       0.11196 NaN     0.11196 0.11196 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ======================================= ========
task               sent                                    received
read_source_models converter=10.23 KB fnames=2.82 KB       48.41 KB
split_filter       srcs=16.38 KB srcfilter=253 B seed=14 B 24.15 KB
================== ======================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 1.13138  0.08203   27    
total split_filter       0.11196  0.23047   1     
======================== ======== ========= ======