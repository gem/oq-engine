Classical PSHA QA test
======================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_66979.hdf5 Wed Nov  9 08:14:53 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

num_sites = 21, sitecol = 1.62 KB

Parameters
----------
============================ ================================
calculation_mode             'classical'                     
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           50.0                            
ses_per_logic_tree_path      1                               
truncation_level             3.0                             
rupture_mesh_spacing         4.0                             
complex_fault_mesh_spacing   4.0                             
width_of_mfd_bin             0.1                             
area_source_discretization   10.0                            
random_seed                  23                              
master_seed                  0                               
sites_per_tile               10000                           
============================ ================================

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
0      BooreAtkinson2008() ChiouYoungs2008() rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
1      BooreAtkinson2008() ChiouYoungs2008() rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
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
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 178         1958         1,958       
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 210         2310         2,310       
============================= ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      388  
#eff_ruptures 4,268
#tot_ruptures 4,268
#tot_weight   4,268
============= =====

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,511       
count_eff_ruptures_num_tasks             22          
count_eff_ruptures_sent.gsims            3,696       
count_eff_ruptures_sent.monitor          27,984      
count_eff_ruptures_sent.sitecol          18,326      
count_eff_ruptures_sent.sources          1,728,234   
count_eff_ruptures_tot_received          33,242      
hazard.input_weight                      4,268       
hazard.n_imts                            2           
hazard.n_levels                          26          
hazard.n_realizations                    4           
hazard.n_sites                           21          
hazard.n_sources                         388         
hazard.output_weight                     2,184       
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
1      97_0      CharacteristicFaultSource 11           0.0       17        0        
0      54_1      CharacteristicFaultSource 11           0.0       9         0        
1      53_0      CharacteristicFaultSource 11           0.0       5         0        
1      98_1      CharacteristicFaultSource 11           0.0       15        0        
1      98_0      CharacteristicFaultSource 11           0.0       15        0        
0      28_1      CharacteristicFaultSource 11           0.0       9         0        
1      79_1      CharacteristicFaultSource 11           0.0       4         0        
0      9_0       CharacteristicFaultSource 11           0.0       16        0        
1      118_0     CharacteristicFaultSource 11           0.0       11        0        
0      15_1      CharacteristicFaultSource 11           0.0       3         0        
1      35_1      CharacteristicFaultSource 11           0.0       9         0        
0      61_0      CharacteristicFaultSource 11           0.0       21        0        
1      15_0      CharacteristicFaultSource 11           0.0       19        0        
1      90_1      CharacteristicFaultSource 11           0.0       9         0        
0      36_0      CharacteristicFaultSource 11           0.0       17        0        
0      41_0      CharacteristicFaultSource 11           0.0       4         0        
1      104_1     CharacteristicFaultSource 11           0.0       10        0        
0      45_1      CharacteristicFaultSource 11           0.0       16        0        
1      101_0     CharacteristicFaultSource 11           0.0       11        0        
0      50_1      CharacteristicFaultSource 11           0.0       21        0        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.0       388   
========================= ========= ======

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.002 4.324E-04 0.001 0.003 22       
================== ===== ========= ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   1.792     0.0       1     
filtering composite source model 0.338     0.0       1     
managing sources                 0.084     0.0       1     
total count_eff_ruptures         0.045     0.0       22    
store source_info                0.003     0.0       1     
aggregate curves                 3.438E-04 0.0       22    
reading site collection          1.171E-04 0.0       1     
saving probability maps          2.813E-05 0.0       1     
================================ ========= ========= ======