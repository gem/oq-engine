Classical PSHA QA test
======================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_1811.hdf5 Fri Jul  7 07:32:37 2017
checksum32                                      2,024,827,974           
engine_version                                  2.6.0-git50066b9        
=============================================== ========================

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
============================== ==================================================================================
count_eff_ruptures.received    tot 18.73 KB, max_per_task 953 B                                                  
count_eff_ruptures.sent        sources 1.34 MB, srcfilter 25.51 KB, param 17.68 KB, monitor 6.6 KB, gsims 3.67 KB
hazard.input_weight            3894.0                                                                            
hazard.n_imts                  2                                                                                 
hazard.n_levels                26                                                                                
hazard.n_realizations          4                                                                                 
hazard.n_sites                 21                                                                                
hazard.n_sources               354                                                                               
hazard.output_weight           546.0                                                                             
hostname                       tstation.gem.lan                                                                  
require_epsilons               False                                                                             
============================== ==================================================================================

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
1      79_0      CharacteristicFaultSource 11           0.006     3         1        
1      100_1     CharacteristicFaultSource 11           0.005     13        1        
1      103_0     CharacteristicFaultSource 11           0.004     11        1        
0      2_0       CharacteristicFaultSource 11           0.004     5         1        
0      1_0       CharacteristicFaultSource 11           0.004     6         1        
0      47_0      CharacteristicFaultSource 11           0.004     7         1        
0      63_0      CharacteristicFaultSource 11           0.004     17        1        
0      80_0      CharacteristicFaultSource 11           0.004     9         1        
0      81_0      CharacteristicFaultSource 11           0.004     6         1        
0      0_0       CharacteristicFaultSource 11           0.004     8         1        
0      20_0      CharacteristicFaultSource 11           0.004     2         1        
0      48_0      CharacteristicFaultSource 11           0.004     6         1        
0      2_1       CharacteristicFaultSource 11           0.004     5         1        
0      1_1       CharacteristicFaultSource 11           0.004     6         1        
0      39_1      CharacteristicFaultSource 11           0.004     7         1        
0      47_1      CharacteristicFaultSource 11           0.004     7         1        
0      39_0      CharacteristicFaultSource 11           0.003     7         1        
0      71_0      CharacteristicFaultSource 11           0.003     18        1        
0      38_1      CharacteristicFaultSource 11           0.003     11        1        
0      20_1      CharacteristicFaultSource 11           0.003     2         1        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.907     354   
========================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.045 0.013  0.009 0.057 21       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 1.881     0.0       1     
total count_eff_ruptures       0.939     0.219     21    
prefiltering source model      0.575     0.0       1     
managing sources               0.078     0.0       1     
store source_info              0.006     0.0       1     
aggregate curves               7.715E-04 0.0       21    
reading site collection        2.234E-04 0.0       1     
saving probability maps        2.670E-05 0.0       1     
============================== ========= ========= ======