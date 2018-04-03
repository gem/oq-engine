Classical PSHA QA test
======================

============== ===================
checksum32     2,024,827,974      
date           2018-03-26T15:55:44
engine_version 2.10.0-git543cfb0  
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
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 1,903        1,980       
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 2,057        2,706       
============================= ====== ==================== ============ ============

============= ======
#TRT models   2     
#eff_ruptures 3,960 
#tot_ruptures 4,686 
#tot_weight   24,251
============= ======

Slowest sources
---------------
========= ========================= ============ ========= ========== ========= =========
source_id source_class              num_ruptures calc_time split_time num_sites num_split
========= ========================= ============ ========= ========== ========= =========
58_1      CharacteristicFaultSource 11           0.027     9.537E-07  17        2        
56_0      CharacteristicFaultSource 11           0.027     1.192E-06  23        2        
63_1      CharacteristicFaultSource 11           0.021     9.537E-07  17        1        
57_0      CharacteristicFaultSource 11           0.020     1.192E-06  22        2        
70_1      CharacteristicFaultSource 11           0.019     1.192E-06  31        2        
38_0      CharacteristicFaultSource 11           0.014     1.192E-06  16        2        
33_0      CharacteristicFaultSource 11           0.013     9.537E-07  30        2        
42_0      CharacteristicFaultSource 11           0.012     1.192E-06  19        2        
30_0      CharacteristicFaultSource 11           0.012     1.192E-06  14        2        
53_0      CharacteristicFaultSource 11           0.012     9.537E-07  16        2        
48_0      CharacteristicFaultSource 11           0.012     1.192E-06  10        2        
45_0      CharacteristicFaultSource 11           0.012     1.192E-06  26        2        
68_0      CharacteristicFaultSource 11           0.011     1.192E-06  28        2        
36_1      CharacteristicFaultSource 11           0.011     1.192E-06  22        2        
33_1      CharacteristicFaultSource 11           0.011     1.192E-06  30        2        
38_1      CharacteristicFaultSource 11           0.010     1.192E-06  16        2        
54_0      CharacteristicFaultSource 11           0.010     1.192E-06  10        2        
39_0      CharacteristicFaultSource 11           0.010     9.537E-07  11        2        
36_0      CharacteristicFaultSource 11           0.010     9.537E-07  22        2        
39_1      CharacteristicFaultSource 11           0.010     1.192E-06  11        2        
========= ========================= ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 1.448     246   
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.027 0.014  0.003 0.060 58       
================== ===== ====== ===== ===== =========

Informational data
------------------
============== ================================================================================== ========
task           sent                                                                               received
count_ruptures sources=1.37 MB srcfilter=102.24 KB param=38.29 KB monitor=18.69 KB gsims=12.46 KB 40.81 KB
============== ================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 2.104     0.0       1     
total count_ruptures           1.580     3.434     58    
managing sources               0.640     0.0       1     
store source_info              0.006     0.0       1     
unpickling count_ruptures      0.003     0.0       58    
aggregate curves               0.002     0.0       58    
splitting sources              0.002     0.0       1     
reading site collection        9.003E-04 0.0       1     
saving probability maps        3.004E-05 0.0       1     
============================== ========= ========= ======