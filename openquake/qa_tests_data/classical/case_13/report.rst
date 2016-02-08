Classical PSHA QA test
======================

num_sites = 21, sitecol = 1.57 KB

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200      
investigation_time           50       
ses_per_logic_tree_path      1        
truncation_level             3.000    
rupture_mesh_spacing         4.000    
complex_fault_mesh_spacing   4.000    
width_of_mfd_bin             0.100    
area_source_discretization   10       
random_seed                  23       
master_seed                  0        
concurrent_tasks             16       
sites_per_tile               1000     
============================ =========

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
aFault_aPriori_D2.1       0.50   `aFault_aPriori_D2.1.xml <aFault_aPriori_D2.1.xml>`_             simple(2)       2/2             
bFault_stitched_D2.1_Char 0.50   `bFault_stitched_D2.1_Char.xml <bFault_stitched_D2.1_Char.xml>`_ simple(2)       2/2             
========================= ====== ================================================================ =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================= =========== ======================= =================
trt_id gsims                             distances   siteparams              ruptparams       
====== ================================= =========== ======================= =================
0      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
1      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== ================================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  0,BooreAtkinson2008: ['<0,aFault_aPriori_D2.1,BooreAtkinson2008,w=0.25>']
  0,ChiouYoungs2008: ['<1,aFault_aPriori_D2.1,ChiouYoungs2008,w=0.25>']
  1,BooreAtkinson2008: ['<2,bFault_stitched_D2.1_Char,BooreAtkinson2008,w=0.25>']
  1,ChiouYoungs2008: ['<3,bFault_stitched_D2.1_Char,ChiouYoungs2008,w=0.25>']>

Number of ruptures per tectonic region type
-------------------------------------------
============================= ====== ==================== =========== ============ ======
source_model                  trt_id trt                  num_sources eff_ruptures weight
============================= ====== ==================== =========== ============ ======
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 168         1,848        1,848 
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 186         2,046        2,046 
============================= ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        354  
#eff_ruptures   3,894
filtered_weight 3,894
=============== =====

Expected data transfer for the sources
--------------------------------------
=========================== =======
Number of tasks to generate 15     
Sent data                   1.33 MB
=========================== =======

Slowest sources
---------------
============ ========= ==================== ====== ========= =========== ========== =========
trt_model_id source_id source_class         weight split_num filter_time split_time calc_time
============ ========= ==================== ====== ========= =========== ========== =========
0            52_1      CharacteristicFaultS 11     1         0.003       0.0        0.0      
0            31_1      CharacteristicFaultS 11     1         0.003       0.0        0.0      
0            28_1      CharacteristicFaultS 11     1         0.003       0.0        0.0      
0            31_0      CharacteristicFaultS 11     1         0.003       0.0        0.0      
0            37_1      CharacteristicFaultS 11     1         0.003       0.0        0.0      
0            40_1      CharacteristicFaultS 11     1         0.003       0.0        0.0      
0            39_1      CharacteristicFaultS 11     1         0.003       0.0        0.0      
0            20_1      CharacteristicFaultS 11     1         0.003       0.0        0.0      
0            49_1      CharacteristicFaultS 11     1         0.003       0.0        0.0      
0            26_1      CharacteristicFaultS 11     1         0.003       0.0        0.0      
0            45_0      CharacteristicFaultS 11     1         0.003       0.0        0.0      
0            2_1       CharacteristicFaultS 11     1         0.003       0.0        0.0      
1            41_1      CharacteristicFaultS 11     1         0.002       0.0        0.0      
1            31_1      CharacteristicFaultS 11     1         0.002       0.0        0.0      
0            51_0      CharacteristicFaultS 11     1         0.002       0.0        0.0      
1            46_0      CharacteristicFaultS 11     1         0.002       0.0        0.0      
0            35_1      CharacteristicFaultS 11     1         0.002       0.0        0.0      
1            54_1      CharacteristicFaultS 11     1         0.002       0.0        0.0      
0            22_1      CharacteristicFaultS 11     1         0.002       0.0        0.0      
1            46_1      CharacteristicFaultS 11     1         0.002       0.0        0.0      
============ ========= ==================== ====== ========= =========== ========== =========