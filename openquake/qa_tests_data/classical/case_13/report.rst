Classical PSHA QA test
======================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_54406.hdf5 Tue Sep 27 14:06:37 2016
engine_version                                 2.1.0-git1ca7123        
hazardlib_version                              0.21.0-git9261682       
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
============================= ====== ==================== =========== ============ ======
source_model                  grp_id trt                  num_sources eff_ruptures weight
============================= ====== ==================== =========== ============ ======
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 180         1980         1,980 
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 246         2706         2,706 
============================= ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        426  
#eff_ruptures   4,686
filtered_weight 4,686
=============== =====

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,495       
count_eff_ruptures_num_tasks             21          
count_eff_ruptures_sent.gsims            3,528       
count_eff_ruptures_sent.monitor          26,775      
count_eff_ruptures_sent.sitecol          17,493      
count_eff_ruptures_sent.sources          1,851,357   
count_eff_ruptures_tot_received          31,335      
hazard.input_weight                      4,686       
hazard.n_imts                            2           
hazard.n_levels                          26          
hazard.n_realizations                    4           
hazard.n_sites                           21          
hazard.n_sources                         426         
hazard.output_weight                     2,184       
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
====== ========= ========================= ====== ========= =========
grp_id source_id source_class              weight calc_time num_sites
====== ========= ========================= ====== ========= =========
1      97_0      CharacteristicFaultSource 11     0.0       0        
0      54_1      CharacteristicFaultSource 11     0.0       0        
1      53_0      CharacteristicFaultSource 11     0.0       0        
1      98_1      CharacteristicFaultSource 11     0.0       0        
1      98_0      CharacteristicFaultSource 11     0.0       0        
0      28_1      CharacteristicFaultSource 11     0.0       0        
1      79_1      CharacteristicFaultSource 11     0.0       0        
0      9_0       CharacteristicFaultSource 11     0.0       0        
1      118_0     CharacteristicFaultSource 11     0.0       0        
0      15_1      CharacteristicFaultSource 11     0.0       0        
1      35_1      CharacteristicFaultSource 11     0.0       0        
1      74_0      CharacteristicFaultSource 11     0.0       0        
0      61_0      CharacteristicFaultSource 11     0.0       0        
1      15_0      CharacteristicFaultSource 11     0.0       0        
1      90_1      CharacteristicFaultSource 11     0.0       0        
0      36_0      CharacteristicFaultSource 11     0.0       0        
0      41_0      CharacteristicFaultSource 11     0.0       0        
1      104_1     CharacteristicFaultSource 11     0.0       0        
0      45_1      CharacteristicFaultSource 11     0.0       0        
1      101_0     CharacteristicFaultSource 11     0.0       0        
====== ========= ========================= ====== ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.0       426   
========================= ========= ======

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.002 5.175E-04 0.001 0.003 21       
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 1.915     0.0       1     
managing sources               0.078     0.0       1     
total count_eff_ruptures       0.049     0.0       21    
store source_info              0.003     0.0       1     
aggregate curves               2.651E-04 0.0       21    
reading site collection        1.321E-04 0.0       1     
saving probability maps        2.098E-05 0.0       1     
============================== ========= ========= ======