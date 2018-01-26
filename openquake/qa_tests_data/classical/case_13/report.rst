Classical PSHA QA test
======================

============== ===================
checksum32     2,024,827,974      
date           2018-01-11T04:54:24
engine_version 2.9.0-git3c583c4   
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
============================= ====== ==================== ============ ============
source_model                  grp_id trt                  eff_ruptures tot_ruptures
============================= ====== ==================== ============ ============
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 3,564        1,980       
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 3,289        2,706       
============================= ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 6,853
#tot_ruptures 4,686
#tot_weight   0    
============= =====

Informational data
------------------
======================= ===================================================================================
count_ruptures.received tot 28.65 KB, max_per_task 3.46 KB                                                 
count_ruptures.sent     sources 1.34 MB, srcfilter 37.02 KB, param 13.86 KB, monitor 6.54 KB, gsims 3.67 KB
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
31_0      CharacteristicFaultSource 11           0.034     12        3        
70_0      CharacteristicFaultSource 11           0.022     19        3        
88_0      CharacteristicFaultSource 11           0.021     17        3        
122_1     CharacteristicFaultSource 11           0.016     12        2        
82_0      CharacteristicFaultSource 11           0.012     9         4        
0_0       CharacteristicFaultSource 11           0.012     8         4        
0_1       CharacteristicFaultSource 11           0.011     8         4        
82_1      CharacteristicFaultSource 11           0.011     9         4        
80_0      CharacteristicFaultSource 11           0.011     9         4        
42_0      CharacteristicFaultSource 11           0.011     18        4        
38_0      CharacteristicFaultSource 11           0.010     11        3        
13_0      CharacteristicFaultSource 11           0.010     7         4        
30_0      CharacteristicFaultSource 11           0.010     9         4        
13_1      CharacteristicFaultSource 11           0.010     7         4        
30_1      CharacteristicFaultSource 11           0.010     9         4        
1_0       CharacteristicFaultSource 11           0.010     9         4        
84_1      CharacteristicFaultSource 11           0.010     12        4        
60_0      CharacteristicFaultSource 11           0.010     7         4        
84_0      CharacteristicFaultSource 11           0.010     12        4        
1_1       CharacteristicFaultSource 11           0.010     9         4        
========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 1.416     246   
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.069 0.055  0.009 0.236 21       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 1.867     0.0       1     
total count_ruptures           1.454     2.777     21    
managing sources               0.619     0.0       1     
store source_info              0.011     0.0       1     
aggregate curves               0.001     0.0       21    
reading site collection        2.818E-04 0.0       1     
saving probability maps        5.126E-05 0.0       1     
============================== ========= ========= ======