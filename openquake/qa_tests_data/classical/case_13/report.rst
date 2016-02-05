Classical PSHA QA test
======================

num_sites = 21, sitecol = 1.57 KB

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           50.0     
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         4.0      
complex_fault_mesh_spacing   4.0      
width_of_mfd_bin             0.1      
area_source_discretization   10.0     
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

  <RlzsAssoc(4)
  0,BooreAtkinson2008: ['<0,aFault_aPriori_D2.1,BooreAtkinson2008,w=0.25>']
  0,ChiouYoungs2008: ['<1,aFault_aPriori_D2.1,ChiouYoungs2008,w=0.25>']
  1,BooreAtkinson2008: ['<2,bFault_stitched_D2.1_Char,BooreAtkinson2008,w=0.25>']
  1,ChiouYoungs2008: ['<3,bFault_stitched_D2.1_Char,ChiouYoungs2008,w=0.25>']>

Number of ruptures per tectonic region type
-------------------------------------------
============================= ====== ==================== =========== ============ ======
source_model                  trt_id trt                  num_sources eff_ruptures weight
============================= ====== ==================== =========== ============ ======
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 168         1848         1848.0
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 186         2046         2046.0
============================= ====== ==================== =========== ============ ======

=============== ======
#TRT models     2     
#sources        354   
#eff_ruptures   3894  
filtered_weight 3894.0
=============== ======

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
0            22_0      CharacteristicFaultS 11.0   1         0.003057    0.0        0.0      
0            22_1      CharacteristicFaultS 11.0   1         0.00281     0.0        0.0      
0            23_0      CharacteristicFaultS 11.0   1         0.00272584  0.0        0.0      
0            23_1      CharacteristicFaultS 11.0   1         0.002707    0.0        0.0      
0            52_1      CharacteristicFaultS 11.0   1         0.00218701  0.0        0.0      
0            0_0       CharacteristicFaultS 11.0   1         0.00186086  0.0        0.0      
0            53_0      CharacteristicFaultS 11.0   1         0.00168204  0.0        0.0      
0            54_1      CharacteristicFaultS 11.0   1         0.00165987  0.0        0.0      
0            55_0      CharacteristicFaultS 11.0   1         0.00165009  0.0        0.0      
0            45_0      CharacteristicFaultS 11.0   1         0.0016439   0.0        0.0      
0            87_1      CharacteristicFaultS 11.0   1         0.00164318  0.0        0.0      
0            56_0      CharacteristicFaultS 11.0   1         0.00163794  0.0        0.0      
0            55_1      CharacteristicFaultS 11.0   1         0.00163794  0.0        0.0      
1            108_0     CharacteristicFaultS 11.0   1         0.00163579  0.0        0.0      
1            46_1      CharacteristicFaultS 11.0   1         0.00162411  0.0        0.0      
0            57_1      CharacteristicFaultS 11.0   1         0.00162101  0.0        0.0      
0            89_0      CharacteristicFaultS 11.0   1         0.00161505  0.0        0.0      
0            88_1      CharacteristicFaultS 11.0   1         0.00161386  0.0        0.0      
1            59_1      CharacteristicFaultS 11.0   1         0.00161314  0.0        0.0      
1            14_1      CharacteristicFaultS 11.0   1         0.0016129   0.0        0.0      
============ ========= ==================== ====== ========= =========== ========== =========