Classical PSHA QA test
======================

============== ===================
checksum32     2,024,827,974      
date           2017-11-08T18:06:57
engine_version 2.8.0-gite3d0f56   
============== ===================

num_sites = 21, num_imts = 2

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ================================================================
Name                    File                                                            
======================= ================================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                    
job_ini                 `job.ini <job.ini>`_                                            
sites                   `qa_sites.csv <qa_sites.csv>`_                                  
source                  `aFault_aPriori_D2.1.xml <aFault_aPriori_D2.1.xml>`_            
source                  `bFault_stitched_D2.1_Char.xml <bFault_stitched_D2.1_Char.xml>`_
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_    
======================= ================================================================

Composite source model
----------------------
========================= ====== =============== ================
smlt_path                 weight gsim_logic_tree num_realizations
========================= ====== =============== ================
aFault_aPriori_D2.1       0.500  simple(2)       2/2             
bFault_stitched_D2.1_Char 0.500  simple(2)       2/2             
========================= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  0,BooreAtkinson2008(): [0]
  0,ChiouYoungs2008(): [1]
  1,BooreAtkinson2008(): [2]
  1,ChiouYoungs2008(): [3]>

Number of ruptures per tectonic region type
-------------------------------------------
============================= ====== ==================== =========== ============ ============
source_model                  grp_id trt                  num_sources eff_ruptures tot_ruptures
============================= ====== ==================== =========== ============ ============
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 168         1,848        1,848       
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 186         2,046        2,046       
============================= ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      354  
#eff_ruptures 3,894
#tot_ruptures 3,894
#tot_weight   0    
============= =====

Informational data
------------------
=========================== ====================================================================================
count_eff_ruptures.received tot 42.02 KB, max_per_task 1.07 KB                                                  
count_eff_ruptures.sent     sources 1.37 MB, srcfilter 66.82 KB, param 45.65 KB, monitor 17.62 KB, gsims 9.61 KB
hazard.input_weight         40216.0                                                                             
hazard.n_imts               2                                                                                   
hazard.n_levels             26                                                                                  
hazard.n_realizations       4                                                                                   
hazard.n_sites              21                                                                                  
hazard.n_sources            354                                                                                 
hazard.output_weight        546.0                                                                               
hostname                    tstation.gem.lan                                                                    
require_epsilons            False                                                                               
=========================== ====================================================================================

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
0      40_1      CharacteristicFaultSource 11           0.021     6         1        
1      83_0      CharacteristicFaultSource 11           0.018     10        1        
0      2_1       CharacteristicFaultSource 11           0.012     5         1        
1      78_1      CharacteristicFaultSource 11           0.005     2         1        
0      2_0       CharacteristicFaultSource 11           0.004     5         1        
0      39_1      CharacteristicFaultSource 11           0.004     7         1        
0      19_0      CharacteristicFaultSource 11           0.004     5         1        
0      34_1      CharacteristicFaultSource 11           0.004     17        1        
0      26_1      CharacteristicFaultSource 11           0.004     9         1        
0      36_0      CharacteristicFaultSource 11           0.004     14        1        
0      12_0      CharacteristicFaultSource 11           0.004     15        1        
0      32_1      CharacteristicFaultSource 11           0.004     12        1        
0      19_1      CharacteristicFaultSource 11           0.004     5         1        
0      40_0      CharacteristicFaultSource 11           0.004     6         1        
0      1_0       CharacteristicFaultSource 11           0.004     6         1        
0      13_0      CharacteristicFaultSource 11           0.004     7         1        
0      56_1      CharacteristicFaultSource 11           0.004     19        1        
0      36_1      CharacteristicFaultSource 11           0.004     14        1        
0      13_1      CharacteristicFaultSource 11           0.004     7         1        
0      10_0      CharacteristicFaultSource 11           0.003     11        1        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.920     354   
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.018 0.009  0.005 0.047 55       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 1.913     0.0       1     
total count_eff_ruptures       0.970     0.0       55    
prefiltering source model      0.592     0.0       1     
managing sources               0.059     0.0       1     
store source_info              0.005     0.0       1     
aggregate curves               0.001     0.0       55    
reading site collection        2.546E-04 0.0       1     
saving probability maps        2.384E-05 0.0       1     
============================== ========= ========= ======