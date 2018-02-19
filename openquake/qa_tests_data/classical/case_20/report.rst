Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     3,909,444,611      
date           2018-02-19T09:59:18
engine_version 2.9.0-gitb536198   
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
random_seed                     106               
master_seed                     0                 
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
========================= ====== =============== ================
smlt_path                 weight gsim_logic_tree num_realizations
========================= ====== =============== ================
sm1_sg1_cog1_char_complex 0.070  trivial(1)      1/1             
sm1_sg1_cog1_char_plane   0.105  trivial(1)      1/1             
sm1_sg1_cog1_char_simple  0.175  trivial(1)      1/1             
sm1_sg1_cog2_char_complex 0.070  trivial(1)      1/1             
sm1_sg1_cog2_char_plane   0.105  trivial(1)      1/1             
sm1_sg1_cog2_char_simple  0.175  trivial(1)      1/1             
sm1_sg2_cog1_char_complex 0.030  trivial(1)      1/1             
sm1_sg2_cog1_char_plane   0.045  trivial(1)      1/1             
sm1_sg2_cog1_char_simple  0.075  trivial(1)      1/1             
sm1_sg2_cog2_char_complex 0.030  trivial(1)      1/1             
sm1_sg2_cog2_char_plane   0.045  trivial(1)      1/1             
sm1_sg2_cog2_char_simple  0.075  trivial(1)      1/1             
========================= ====== =============== ================

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
source_model.xml 0      Active Shallow Crust 97           86          
source_model.xml 1      Active Shallow Crust 153          86          
source_model.xml 2      Active Shallow Crust 153          86          
source_model.xml 3      Active Shallow Crust 186          86          
source_model.xml 4      Active Shallow Crust 186          86          
source_model.xml 5      Active Shallow Crust 186          86          
source_model.xml 6      Active Shallow Crust 155          86          
source_model.xml 7      Active Shallow Crust 155          86          
source_model.xml 8      Active Shallow Crust 155          86          
source_model.xml 9      Active Shallow Crust 188          86          
source_model.xml 10     Active Shallow Crust 188          86          
source_model.xml 11     Active Shallow Crust 188          86          
================ ====== ==================== ============ ============

============= =====
#TRT models   12   
#eff_ruptures 1,990
#tot_ruptures 1,032
#tot_weight   2,880
============= =====

Informational data
------------------
======================= ===================================================================================
count_ruptures.received tot 19.29 KB, max_per_task 976 B                                                   
count_ruptures.sent     sources 45.71 KB, srcfilter 16.92 KB, param 9.98 KB, monitor 7.48 KB, gsims 2.81 KB
hazard.input_weight     2880.0                                                                             
hazard.n_imts           1                                                                                  
hazard.n_levels         4                                                                                  
hazard.n_realizations   12                                                                                 
hazard.n_sites          1                                                                                  
hazard.n_sources        36                                                                                 
hazard.output_weight    4.0                                                                                
hostname                tstation.gem.lan                                                                   
require_epsilons        False                                                                              
======================= ===================================================================================

Slowest sources
---------------
========= ========================= ============ ========= ========= =========
source_id source_class              num_ruptures calc_time num_sites num_split
========= ========================= ============ ========= ========= =========
CHAR1     CharacteristicFaultSource 1            0.216     145       144      
SFLT1     SimpleFaultSource         58           0.061     24        23       
COMFLT1   ComplexFaultSource        62           0.029     13        12       
========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.216     1     
ComplexFaultSource        0.029     1     
SimpleFaultSource         0.061     1     
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.014 0.048  0.002 0.240 24       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.641     0.0       1     
total count_ruptures           0.328     0.246     24    
managing sources               0.084     0.0       1     
store source_info              0.009     0.0       1     
aggregate curves               4.063E-04 0.0       24    
saving probability maps        5.531E-05 0.0       1     
reading site collection        4.554E-05 0.0       1     
============================== ========= ========= ======