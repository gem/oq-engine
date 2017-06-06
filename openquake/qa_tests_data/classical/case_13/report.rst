Classical PSHA QA test
======================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_26061.hdf5 Tue Jun  6 14:58:28 2017
engine_version                                   2.5.0-gitb270b98        
hazardlib_version                                0.25.0-git6276f16       
================================================ ========================

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
count_eff_ruptures.received    tot 18.47 KB, max_per_task 941 B                                                   
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
0      55_0      CharacteristicFaultSource 11           0.020     6         1        
0      9_0       CharacteristicFaultSource 11           0.019     14        1        
0      58_0      CharacteristicFaultSource 11           0.008     13        1        
1      108_0     CharacteristicFaultSource 11           0.006     15        1        
1      111_0     CharacteristicFaultSource 11           0.006     5         1        
1      72_0      CharacteristicFaultSource 11           0.006     13        1        
0      0_0       CharacteristicFaultSource 11           0.004     8         1        
0      2_0       CharacteristicFaultSource 11           0.004     5         1        
0      47_0      CharacteristicFaultSource 11           0.004     7         1        
0      39_0      CharacteristicFaultSource 11           0.004     7         1        
0      38_0      CharacteristicFaultSource 11           0.004     11        1        
0      80_0      CharacteristicFaultSource 11           0.004     9         1        
0      89_0      CharacteristicFaultSource 11           0.004     12        1        
0      63_0      CharacteristicFaultSource 11           0.004     17        1        
0      1_0       CharacteristicFaultSource 11           0.004     6         1        
0      2_1       CharacteristicFaultSource 11           0.004     5         1        
0      48_0      CharacteristicFaultSource 11           0.004     6         1        
0      0_1       CharacteristicFaultSource 11           0.004     8         1        
0      47_1      CharacteristicFaultSource 11           0.004     7         1        
0      38_1      CharacteristicFaultSource 11           0.004     11        1        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.934     354   
========================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.046 0.013  0.015 0.073 21       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 1.807     0.0       1     
total count_eff_ruptures       0.971     0.0       21    
prefiltering source model      0.589     3.609     1     
managing sources               0.043     0.0       1     
store source_info              0.008     0.0       1     
aggregate curves               0.001     0.0       21    
reading site collection        1.729E-04 0.0       1     
saving probability maps        3.409E-05 0.0       1     
============================== ========= ========= ======