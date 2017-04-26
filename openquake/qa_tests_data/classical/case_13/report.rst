Classical PSHA QA test
======================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7598.hdf5 Wed Apr 26 15:54:55 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 21, sitecol = 1.84 KB

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
========================= ====== ================================================================ =============== ================
smlt_path                 weight source_model_file                                                gsim_logic_tree num_realizations
========================= ====== ================================================================ =============== ================
aFault_aPriori_D2.1       0.500  `aFault_aPriori_D2.1.xml <aFault_aPriori_D2.1.xml>`_             simple(2)       2/2             
bFault_stitched_D2.1_Char 0.500  `bFault_stitched_D2.1_Char.xml <bFault_stitched_D2.1_Char.xml>`_ simple(2)       2/2             
========================= ====== ================================================================ =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rjb rx rrup vs30 vs30measured z1pt0 dip ztor rake mag
1      BooreAtkinson2008() ChiouYoungs2008() rjb rx rrup vs30 vs30measured z1pt0 dip ztor rake mag
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  0,BooreAtkinson2008(): ['<0,aFault_aPriori_D2.1~BooreAtkinson2008,w=0.25>']
  0,ChiouYoungs2008(): ['<1,aFault_aPriori_D2.1~ChiouYoungs2008,w=0.25>']
  1,BooreAtkinson2008(): ['<2,bFault_stitched_D2.1_Char~BooreAtkinson2008,w=0.25>']
  1,ChiouYoungs2008(): ['<3,bFault_stitched_D2.1_Char~ChiouYoungs2008,w=0.25>']>

Number of ruptures per tectonic region type
-------------------------------------------
============================= ====== ==================== =========== ============ ============
source_model                  grp_id trt                  num_sources eff_ruptures tot_ruptures
============================= ====== ==================== =========== ============ ============
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 168         1848         1,848       
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 186         2002         2,046       
============================= ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      354  
#eff_ruptures 3,850
#tot_ruptures 3,894
#tot_weight   3,894
============= =====

Informational data
------------------
============================== ===================================================================================
count_eff_ruptures.received    tot 27.3 KB, max_per_task 1.3 KB                                                   
count_eff_ruptures.sent        sources 1.37 MB, srcfilter 25.51 KB, monitor 22.74 KB, gsims 3.67 KB, param 1.33 KB
hazard.input_weight            3,894                                                                              
hazard.n_imts                  2 B                                                                                
hazard.n_levels                26 B                                                                               
hazard.n_realizations          4 B                                                                                
hazard.n_sites                 21 B                                                                               
hazard.n_sources               354 B                                                                              
hazard.output_weight           2,184                                                                              
hostname                       tstation.gem.lan                                                                   
require_epsilons               0 B                                                                                
============================== ===================================================================================

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
0      83_1      CharacteristicFaultSource 11           0.0       8         0        
0      29_1      CharacteristicFaultSource 11           0.0       12        0        
0      43_0      CharacteristicFaultSource 11           0.0       18        0        
0      78_0      CharacteristicFaultSource 11           0.0       5         0        
1      36_1      CharacteristicFaultSource 11           0.0       8         0        
0      80_1      CharacteristicFaultSource 11           0.0       9         0        
1      89_1      CharacteristicFaultSource 11           0.0       16        0        
0      34_1      CharacteristicFaultSource 11           0.0       17        0        
0      31_0      CharacteristicFaultSource 11           0.0       12        0        
0      22_1      CharacteristicFaultSource 11           0.0       2         0        
1      89_0      CharacteristicFaultSource 11           0.0       16        0        
1      46_0      CharacteristicFaultSource 11           0.0       7         0        
1      46_1      CharacteristicFaultSource 11           0.0       7         0        
0      69_0      CharacteristicFaultSource 11           0.0       13        0        
1      87_0      CharacteristicFaultSource 11           0.0       15        0        
1      113_0     CharacteristicFaultSource 11           0.0       9         0        
0      66_0      CharacteristicFaultSource 11           0.0       11        0        
1      45_0      CharacteristicFaultSource 11           0.0       13        0        
0      47_0      CharacteristicFaultSource 11           0.0       7         0        
0      60_0      CharacteristicFaultSource 11           0.0       7         0        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.0       354   
========================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.207 0.121  0.045 0.483 21       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         4.346     0.238     21    
reading composite source model   1.975     0.0       1     
filtering composite source model 0.588     0.0       1     
store source_info                0.003     0.0       1     
reading site collection          3.152E-04 0.0       1     
aggregate curves                 2.856E-04 0.0       21    
managing sources                 1.073E-04 0.0       1     
saving probability maps          3.004E-05 0.0       1     
================================ ========= ========= ======