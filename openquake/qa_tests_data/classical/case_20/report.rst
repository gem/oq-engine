Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     3,909,444,611      
date           2017-10-24T05:47:56
engine_version 2.8.0-git8e9cdf8   
============== ===================

num_sites = 1, num_imts = 1

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
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 3           86           86          
source_model.xml 1      Active Shallow Crust 3           86           86          
source_model.xml 2      Active Shallow Crust 3           86           86          
source_model.xml 3      Active Shallow Crust 3           119          119         
source_model.xml 4      Active Shallow Crust 3           119          119         
source_model.xml 5      Active Shallow Crust 3           119          119         
source_model.xml 6      Active Shallow Crust 3           88           88          
source_model.xml 7      Active Shallow Crust 3           88           88          
source_model.xml 8      Active Shallow Crust 3           88           88          
source_model.xml 9      Active Shallow Crust 3           121          121         
source_model.xml 10     Active Shallow Crust 3           121          121         
source_model.xml 11     Active Shallow Crust 3           121          121         
================ ====== ==================== =========== ============ ============

============= =====
#TRT models   12   
#sources      36   
#eff_ruptures 1,242
#tot_ruptures 1,242
#tot_weight   0    
============= =====

Informational data
------------------
=========================== ===================================================================================
count_eff_ruptures.received tot 11.32 KB, max_per_task 678 B                                                   
count_eff_ruptures.sent     sources 99.53 KB, srcfilter 12.02 KB, param 10.76 KB, monitor 5.75 KB, gsims 1.6 KB
hazard.input_weight         2880.0                                                                             
hazard.n_imts               1                                                                                  
hazard.n_levels             4                                                                                  
hazard.n_realizations       12                                                                                 
hazard.n_sites              1                                                                                  
hazard.n_sources            36                                                                                 
hazard.output_weight        4.0                                                                                
hostname                    tstation.gem.lan                                                                   
require_epsilons            False                                                                              
=========================== ===================================================================================

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
3      COMFLT1   ComplexFaultSource        62           0.003     1         1        
2      CHAR1     CharacteristicFaultSource 1            0.003     1         1        
4      COMFLT1   ComplexFaultSource        62           0.003     1         1        
1      SFLT1     SimpleFaultSource         56           0.003     1         1        
4      SFLT1     SimpleFaultSource         56           0.003     1         1        
0      SFLT1     SimpleFaultSource         56           0.003     1         1        
5      CHAR1     CharacteristicFaultSource 1            0.003     1         1        
3      SFLT1     SimpleFaultSource         56           0.003     1         1        
2      SFLT1     SimpleFaultSource         56           0.003     1         1        
5      SFLT1     SimpleFaultSource         56           0.003     1         1        
5      COMFLT1   ComplexFaultSource        62           0.002     1         1        
11     SFLT1     SimpleFaultSource         58           0.002     1         1        
8      SFLT1     SimpleFaultSource         58           0.002     1         1        
3      CHAR1     CharacteristicFaultSource 1            0.002     1         1        
1      CHAR1     CharacteristicFaultSource 1            0.002     1         1        
9      SFLT1     SimpleFaultSource         58           0.002     1         1        
0      COMFLT1   ComplexFaultSource        29           0.002     1         1        
11     CHAR1     CharacteristicFaultSource 1            0.002     1         1        
8      CHAR1     CharacteristicFaultSource 1            0.002     1         1        
1      COMFLT1   ComplexFaultSource        29           0.002     1         1        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.026     12    
ComplexFaultSource        0.027     12    
SimpleFaultSource         0.028     12    
========================= ========= ======

Duplicated sources
------------------
========= ========= =========================
source_id calc_time src_group_ids            
========= ========= =========================
CHAR1     0.026     0 1 2 3 4 5 6 7 8 9 10 11
COMFLT1   0.027     0 1 2 3 4 5 6 7 8 9 10 11
SFLT1     0.028     0 1 2 3 4 5 6 7 8 9 10 11
========= ========= =========================
Sources with the same ID but different parameters

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.005 0.002  0.003 0.008 18       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.580     0.0       1     
total count_eff_ruptures       0.094     0.230     18    
managing sources               0.042     0.0       1     
prefiltering source model      0.035     0.0       1     
store source_info              0.007     0.0       1     
aggregate curves               5.918E-04 0.0       18    
saving probability maps        3.624E-05 0.0       1     
reading site collection        3.052E-05 0.0       1     
============================== ========= ========= ======