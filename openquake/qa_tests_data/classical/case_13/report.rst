Classical PSHA QA test
======================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_29224.hdf5 Wed Jun 14 10:04:18 2017
engine_version                                   2.5.0-gite200a20        
================================================ ========================

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
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
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
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 186         2046         2,046       
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
============================== ===================================================================================
count_eff_ruptures.received    tot 18.48 KB, max_per_task 941 B                                                   
count_eff_ruptures.sent        sources 1.34 MB, srcfilter 25.51 KB, param 17.68 KB, monitor 6.42 KB, gsims 3.67 KB
hazard.input_weight            3,894                                                                              
hazard.n_imts                  2 B                                                                                
hazard.n_levels                26 B                                                                               
hazard.n_realizations          4 B                                                                                
hazard.n_sites                 21 B                                                                               
hazard.n_sources               354 B                                                                              
hazard.output_weight           546                                                                                
hostname                       tstation.gem.lan                                                                   
require_epsilons               0 B                                                                                
============================== ===================================================================================

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
0      60_1      CharacteristicFaultSource 11           0.025     7         1        
1      82_0      CharacteristicFaultSource 11           0.014     6         1        
0      4_1       CharacteristicFaultSource 11           0.013     6         1        
1      41_0      CharacteristicFaultSource 11           0.013     16        1        
0      74_1      CharacteristicFaultSource 11           0.008     19        1        
0      26_0      CharacteristicFaultSource 11           0.007     9         1        
0      0_0       CharacteristicFaultSource 11           0.004     8         1        
0      68_1      CharacteristicFaultSource 11           0.004     17        1        
0      1_0       CharacteristicFaultSource 11           0.004     6         1        
0      2_0       CharacteristicFaultSource 11           0.004     5         1        
1      0_0       CharacteristicFaultSource 11           0.004     8         1        
0      50_0      CharacteristicFaultSource 11           0.004     19        1        
0      71_0      CharacteristicFaultSource 11           0.004     18        1        
1      102_1     CharacteristicFaultSource 11           0.004     11        1        
0      63_0      CharacteristicFaultSource 11           0.004     17        1        
0      38_0      CharacteristicFaultSource 11           0.004     11        1        
0      20_0      CharacteristicFaultSource 11           0.004     2         1        
0      2_1       CharacteristicFaultSource 11           0.004     5         1        
0      39_0      CharacteristicFaultSource 11           0.004     7         1        
0      0_1       CharacteristicFaultSource 11           0.004     8         1        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.921     354   
========================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.045 0.015  0.010 0.073 21       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 2.026     0.0       1     
total count_eff_ruptures       0.955     0.0       21    
prefiltering source model      0.592     0.0       1     
managing sources               0.032     0.0       1     
store source_info              0.007     0.0       1     
aggregate curves               0.001     0.0       21    
reading site collection        2.372E-04 0.0       1     
saving probability maps        3.195E-05 0.0       1     
============================== ========= ========= ======