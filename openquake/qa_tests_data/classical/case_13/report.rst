Classical PSHA QA test
======================

============== ===================
checksum32     2,024,827,974      
date           2018-02-19T09:58:58
engine_version 2.9.0-gitb536198   
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
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 2,651        1,980       
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 2,893        2,706       
============================= ====== ==================== ============ ============

============= ======
#TRT models   2     
#eff_ruptures 5,544 
#tot_ruptures 4,686 
#tot_weight   24,251
============= ======

Informational data
------------------
======================= ======================================================================================
count_ruptures.received tot 66.28 KB, max_per_task 1.75 KB                                                    
count_ruptures.sent     sources 1.37 MB, srcfilter 102.24 KB, param 38.29 KB, monitor 18.07 KB, gsims 12.46 KB
hazard.input_weight     4686.0                                                                                
hazard.n_imts           2                                                                                     
hazard.n_levels         26                                                                                    
hazard.n_realizations   4                                                                                     
hazard.n_sites          21                                                                                    
hazard.n_sources        426                                                                                   
hazard.output_weight    546.0                                                                                 
hostname                tstation.gem.lan                                                                      
require_epsilons        False                                                                                 
======================= ======================================================================================

Slowest sources
---------------
========= ========================= ============ ========= ========= =========
source_id source_class              num_ruptures calc_time num_sites num_split
========= ========================= ============ ========= ========= =========
65_0      CharacteristicFaultSource 11           0.028     30        3        
51_0      CharacteristicFaultSource 11           0.027     37        3        
35_0      CharacteristicFaultSource 11           0.025     26        2        
26_0      CharacteristicFaultSource 11           0.022     19        2        
9_1       CharacteristicFaultSource 11           0.022     29        2        
113_1     CharacteristicFaultSource 11           0.021     10        1        
82_1      CharacteristicFaultSource 11           0.019     31        4        
0_0       CharacteristicFaultSource 11           0.018     33        4        
38_0      CharacteristicFaultSource 11           0.018     33        4        
81_0      CharacteristicFaultSource 11           0.018     21        4        
48_1      CharacteristicFaultSource 11           0.018     15        3        
36_0      CharacteristicFaultSource 11           0.018     37        3        
83_0      CharacteristicFaultSource 11           0.017     37        4        
81_1      CharacteristicFaultSource 11           0.017     21        4        
83_1      CharacteristicFaultSource 11           0.017     37        4        
30_0      CharacteristicFaultSource 11           0.016     20        3        
0_1       CharacteristicFaultSource 11           0.016     25        3        
30_1      CharacteristicFaultSource 11           0.015     20        3        
41_1      CharacteristicFaultSource 11           0.015     41        4        
41_0      CharacteristicFaultSource 11           0.015     41        4        
========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 1.968     246   
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.036 0.027  0.007 0.127 58       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total count_ruptures           2.077     0.195     58    
reading composite source model 1.921     0.0       1     
managing sources               0.744     0.0       1     
store source_info              0.006     0.0       1     
aggregate curves               0.002     0.0       58    
reading site collection        2.165E-04 0.0       1     
saving probability maps        3.123E-05 0.0       1     
============================== ========= ========= ======