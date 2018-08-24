Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     3,909,444,611      
date           2018-06-26T14:57:45
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
========================= ======= =============== ================
smlt_path                 weight  gsim_logic_tree num_realizations
========================= ======= =============== ================
sm1_sg1_cog1_char_complex 0.07000 trivial(1)      1/1             
sm1_sg1_cog1_char_plane   0.10500 trivial(1)      1/1             
sm1_sg1_cog1_char_simple  0.17500 trivial(1)      1/1             
sm1_sg1_cog2_char_complex 0.07000 trivial(1)      1/1             
sm1_sg1_cog2_char_plane   0.10500 trivial(1)      1/1             
sm1_sg1_cog2_char_simple  0.17500 trivial(1)      1/1             
sm1_sg2_cog1_char_complex 0.03000 trivial(1)      1/1             
sm1_sg2_cog1_char_plane   0.04500 trivial(1)      1/1             
sm1_sg2_cog1_char_simple  0.07500 trivial(1)      1/1             
sm1_sg2_cog2_char_complex 0.03000 trivial(1)      1/1             
sm1_sg2_cog2_char_plane   0.04500 trivial(1)      1/1             
sm1_sg2_cog2_char_simple  0.07500 trivial(1)      1/1             
========================= ======= =============== ================

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
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=12, rlzs=12)
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
  11,SadighEtAl1997(): [11]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 87           86          
source_model.xml 1      Active Shallow Crust 143          86          
source_model.xml 2      Active Shallow Crust 143          86          
source_model.xml 3      Active Shallow Crust 176          86          
source_model.xml 4      Active Shallow Crust 176          86          
source_model.xml 5      Active Shallow Crust 176          86          
source_model.xml 6      Active Shallow Crust 145          86          
source_model.xml 7      Active Shallow Crust 147          86          
source_model.xml 8      Active Shallow Crust 147          86          
source_model.xml 9      Active Shallow Crust 180          86          
source_model.xml 10     Active Shallow Crust 180          86          
source_model.xml 11     Active Shallow Crust 179          86          
================ ====== ==================== ============ ============

============= =====
#TRT models   12   
#eff_ruptures 1,879
#tot_ruptures 1,032
#tot_weight   2,880
============= =====

Slowest sources
---------------
========= ========================= ============ ========= ========== ========= ========= ======
source_id source_class              num_ruptures calc_time split_time num_sites num_split events
========= ========================= ============ ========= ========== ========= ========= ======
COMFLT1   ComplexFaultSource        62           0.06728   1.431E-06  1.00000   12        0     
SFLT1     SimpleFaultSource         58           0.05633   1.931E-05  1.00000   46        0     
CHAR1     CharacteristicFaultSource 1            0.00692   1.431E-06  1.00000   23        0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.00692   1     
ComplexFaultSource        0.06728   1     
SimpleFaultSource         0.05633   1     
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00537 0.00282 0.00116 0.01113 48       
count_eff_ruptures 0.00714 0.00206 0.00310 0.00996 25       
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=18, weight=116, duration=0 s, sources="COMFLT1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   116     NaN    116 116 1
======== ======= ====== === === =

Slowest task
------------
taskno=24, weight=248, duration=0 s, sources="COMFLT1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   248     NaN    248 248 1
======== ======= ====== === === =

Data transfer
-------------
================== ================================================================================ =========
task               sent                                                                             received 
RtreeFilter        srcs=119.53 KB monitor=15.09 KB srcfilter=13.08 KB                               124.11 KB
count_eff_ruptures sources=112.33 KB param=10.72 KB monitor=8.03 KB srcfilter=6.01 KB gsims=2.93 KB 9.73 KB  
================== ================================================================================ =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.92526   0.0       1     
managing sources               0.40584   0.0       1     
total prefilter                0.25795   4.74219   48    
total count_eff_ruptures       0.17852   6.39844   25    
unpickling prefilter           0.01731   0.0       48    
store source_info              0.00761   0.0       1     
unpickling count_eff_ruptures  0.00755   0.0       25    
aggregate curves               0.00692   0.0       25    
splitting sources              7.322E-04 0.0       1     
reading site collection        3.412E-04 0.0       1     
============================== ========= ========= ======