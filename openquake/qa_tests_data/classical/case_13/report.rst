Classical PSHA QA test
======================

============== ===================
checksum32     2,024,827,974      
date           2018-02-25T06:42:46
engine_version 2.10.0-git1f7c0c0  
============== ===================

num_sites = 21, num_levels = 26

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
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
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
============================= ====== ==================== ============ ============
source_model                  grp_id trt                  eff_ruptures tot_ruptures
============================= ====== ==================== ============ ============
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 3,531        1,980       
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 3,806        2,706       
============================= ====== ==================== ============ ============

============= ======
#TRT models   2     
#eff_ruptures 7,337 
#tot_ruptures 4,686 
#tot_weight   24,251
============= ======

Informational data
------------------
======================= ===================================================================================
count_ruptures.received tot 39.22 KB, max_per_task 3.09 KB                                                 
count_ruptures.sent     sources 1.34 MB, srcfilter 37.02 KB, param 13.86 KB, monitor 6.77 KB, gsims 4.51 KB
hazard.input_weight     4686.0                                                                             
hazard.n_imts           2                                                                                  
hazard.n_levels         26                                                                                 
hazard.n_realizations   4                                                                                  
hazard.n_sites          21                                                                                 
hazard.n_sources        426                                                                                
hazard.output_weight    546.0                                                                              
hostname                tstation.gem.lan                                                                   
require_epsilons        False                                                                              
======================= ===================================================================================

Slowest sources
---------------
========= ========================= ============ ========= ========= =========
source_id source_class              num_ruptures calc_time num_sites num_split
========= ========================= ============ ========= ========= =========
85_1      CharacteristicFaultSource 11           0.042     51        4        
2_1       CharacteristicFaultSource 11           0.036     37        4        
31_1      CharacteristicFaultSource 11           0.032     37        3        
29_1      CharacteristicFaultSource 11           0.032     25        2        
12_0      CharacteristicFaultSource 11           0.028     37        4        
46_1      CharacteristicFaultSource 11           0.019     37        4        
53_0      CharacteristicFaultSource 11           0.019     33        4        
53_1      CharacteristicFaultSource 11           0.019     33        4        
51_1      CharacteristicFaultSource 11           0.019     45        4        
73_0      CharacteristicFaultSource 11           0.018     57        4        
57_1      CharacteristicFaultSource 11           0.018     45        4        
73_1      CharacteristicFaultSource 11           0.018     57        4        
33_0      CharacteristicFaultSource 11           0.018     61        4        
57_0      CharacteristicFaultSource 11           0.017     45        4        
33_1      CharacteristicFaultSource 11           0.017     61        4        
43_0      CharacteristicFaultSource 11           0.017     69        4        
43_1      CharacteristicFaultSource 11           0.017     69        4        
45_1      CharacteristicFaultSource 11           0.016     53        4        
75_1      CharacteristicFaultSource 11           0.016     51        4        
65_0      CharacteristicFaultSource 11           0.016     43        4        
========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 2.411     246   
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.122 0.037  0.034 0.201 21       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total count_ruptures           2.561     0.145     21    
reading composite source model 2.102     0.0       1     
managing sources               0.627     0.0       1     
store source_info              0.005     0.0       1     
aggregate curves               0.001     0.0       21    
reading site collection        2.086E-04 0.0       1     
saving probability maps        2.527E-05 0.0       1     
============================== ========= ========= ======