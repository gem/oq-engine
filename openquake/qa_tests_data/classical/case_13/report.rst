Classical PSHA QA test
======================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_20752.hdf5 Fri May 12 07:08:06 2017
engine_version                                   2.4.0-git7dc35c5        
hazardlib_version                                0.24.0-git0596dd3       
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
0      BooreAtkinson2008() ChiouYoungs2008() rx rrup rjb vs30 vs30measured z1pt0 dip mag rake ztor
1      BooreAtkinson2008() ChiouYoungs2008() rx rrup rjb vs30 vs30measured z1pt0 dip mag rake ztor
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
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 180         1848         1,980       
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 246         2046         2,706       
============================= ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      426  
#eff_ruptures 3,894
#tot_ruptures 4,686
#tot_weight   4,686
============= =====

Informational data
------------------
============================== =================================================================================
count_eff_ruptures.received    tot 38.2 KB, max_per_task 1.67 KB                                                
count_eff_ruptures.sent        sources 1.5 MB, srcfilter 29.16 KB, monitor 26.02 KB, gsims 4.2 KB, param 1.52 KB
hazard.input_weight            4,686                                                                            
hazard.n_imts                  2 B                                                                              
hazard.n_levels                26 B                                                                             
hazard.n_realizations          4 B                                                                              
hazard.n_sites                 21 B                                                                             
hazard.n_sources               426 B                                                                            
hazard.output_weight           546                                                                              
hostname                       tstation.gem.lan                                                                 
require_epsilons               0 B                                                                              
============================== =================================================================================

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
0      60_0      CharacteristicFaultSource 11           0.029     7         1        
0      75_1      CharacteristicFaultSource 11           0.019     17        1        
0      6_0       CharacteristicFaultSource 11           0.019     6         1        
0      78_1      CharacteristicFaultSource 11           0.019     5         1        
0      87_1      CharacteristicFaultSource 11           0.018     11        1        
0      72_1      CharacteristicFaultSource 11           0.018     17        1        
0      63_1      CharacteristicFaultSource 11           0.018     17        1        
0      9_1       CharacteristicFaultSource 11           0.016     14        1        
0      81_0      CharacteristicFaultSource 11           0.013     6         1        
0      67_1      CharacteristicFaultSource 11           0.010     19        1        
0      0_0       CharacteristicFaultSource 11           0.004     8         1        
0      42_0      CharacteristicFaultSource 11           0.004     1         1        
0      5_1       CharacteristicFaultSource 11           0.004     5         1        
0      42_1      CharacteristicFaultSource 11           0.004     1         1        
0      0_1       CharacteristicFaultSource 11           0.003     8         1        
0      75_0      CharacteristicFaultSource 11           0.003     17        1        
0      26_0      CharacteristicFaultSource 11           0.003     9         1        
0      10_0      CharacteristicFaultSource 11           0.003     11        1        
0      67_0      CharacteristicFaultSource 11           0.003     19        1        
0      10_1      CharacteristicFaultSource 11           0.003     11        1        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.921     426   
========================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.046 0.020  0.025 0.089 24       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   2.020     0.0       1     
total count_eff_ruptures         1.113     0.066     24    
managing sources                 0.074     0.0       1     
store source_info                0.004     0.0       1     
aggregate curves                 0.001     0.0       24    
reading site collection          2.453E-04 0.0       1     
saving probability maps          3.004E-05 0.0       1     
filtering composite source model 2.766E-05 0.0       1     
================================ ========= ========= ======