Classical PSHA QA test
======================

============== ===================
checksum32     2,024,827,974      
date           2018-04-19T05:02:35
engine_version 3.1.0-git9c5da5b   
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
========= ========================= ============ ========= ========== ========= ========= ======
source_id source_class              num_ruptures calc_time split_time num_sites num_split events
========= ========================= ============ ========= ========== ========= ========= ======
51_1      CharacteristicFaultSource 11           0.062     1.907E-06  22        2         0     
44_1      CharacteristicFaultSource 11           0.050     1.907E-06  31        2         0     
58_1      CharacteristicFaultSource 11           0.044     1.907E-06  17        2         0     
47_0      CharacteristicFaultSource 11           0.038     1.907E-06  13        2         0     
84_0      CharacteristicFaultSource 11           0.034     1.907E-06  21        2         0     
49_1      CharacteristicFaultSource 11           0.032     1.669E-06  13        2         0     
62_0      CharacteristicFaultSource 11           0.031     1.907E-06  18        1         0     
111_1     CharacteristicFaultSource 11           0.031     1.907E-06  5         1         0     
100_1     CharacteristicFaultSource 11           0.030     1.907E-06  26        2         0     
30_0      CharacteristicFaultSource 11           0.028     1.669E-06  14        2         0     
87_0      CharacteristicFaultSource 11           0.027     1.907E-06  26        2         0     
40_1      CharacteristicFaultSource 11           0.027     1.907E-06  6         1         0     
12_1      CharacteristicFaultSource 11           0.026     1.907E-06  18        2         0     
80_1      CharacteristicFaultSource 11           0.026     1.669E-06  12        2         0     
34_0      CharacteristicFaultSource 11           0.026     1.907E-06  29        2         0     
73_0      CharacteristicFaultSource 11           0.026     1.907E-06  28        2         0     
1_0       CharacteristicFaultSource 11           0.024     1.907E-06  15        2         0     
55_1      CharacteristicFaultSource 11           0.022     1.907E-06  9         2         0     
14_1      CharacteristicFaultSource 11           0.022     1.907E-06  23        2         0     
81_1      CharacteristicFaultSource 11           0.022     1.907E-06  10        2         0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 1.918     246   
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.035 0.015  0.004 0.075 58       
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
reading composite source model 4.649     0.0       1     
total count_ruptures           2.050     4.238     58    
managing sources               1.305     0.0       1     
store source_info              0.009     0.0       1     
splitting sources              0.004     0.0       1     
unpickling count_ruptures      0.004     0.0       58    
aggregate curves               0.002     0.0       58    
reading site collection        8.333E-04 0.0       1     
saving probability maps        3.767E-05 0.0       1     
============================== ========= ========= ======