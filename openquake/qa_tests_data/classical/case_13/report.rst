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
============================= ====== ==================== =========== ============ ============ ======
source_model                  trt_id trt                  num_sources num_ruptures eff_ruptures weight
============================= ====== ==================== =========== ============ ============ ======
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 168         1980         1848         1848.0
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 186         2706         2046         2046.0
============================= ====== ==================== =========== ============ ============ ======

=============== ======
#TRT models     2     
#sources        354   
#tot_ruptures   4686  
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
0            59_0      CharacteristicFaultS 11.0   1         0.00223613  0.0        0.0      
0            86_1      CharacteristicFaultS 11.0   1         0.00207615  0.0        0.0      
0            59_1      CharacteristicFaultS 11.0   1         0.00196505  0.0        0.0      
0            0_0       CharacteristicFaultS 11.0   1         0.00183201  0.0        0.0      
0            28_1      CharacteristicFaultS 11.0   1         0.00179195  0.0        0.0      
0            87_0      CharacteristicFaultS 11.0   1         0.00178885  0.0        0.0      
1            74_1      CharacteristicFaultS 11.0   1         0.00175095  0.0        0.0      
0            87_1      CharacteristicFaultS 11.0   1         0.00174618  0.0        0.0      
0            88_0      CharacteristicFaultS 11.0   1         0.00166297  0.0        0.0      
0            29_0      CharacteristicFaultS 11.0   1         0.00163698  0.0        0.0      
1            12_0      CharacteristicFaultS 11.0   1         0.00163507  0.0        0.0      
1            119_1     CharacteristicFaultS 11.0   1         0.00163102  0.0        0.0      
0            88_1      CharacteristicFaultS 11.0   1         0.00162983  0.0        0.0      
0            12_0      CharacteristicFaultS 11.0   1         0.00162888  0.0        0.0      
1            107_1     CharacteristicFaultS 11.0   1         0.00162697  0.0        0.0      
0            23_0      CharacteristicFaultS 11.0   1         0.00162196  0.0        0.0      
0            5_0       CharacteristicFaultS 11.0   1         0.00161886  0.0        0.0      
0            29_1      CharacteristicFaultS 11.0   1         0.0016129   0.0        0.0      
0            78_0      CharacteristicFaultS 11.0   1         0.00161195  0.0        0.0      
1            38_0      CharacteristicFaultS 11.0   1         0.00161195  0.0        0.0      
============ ========= ==================== ====== ========= =========== ========== =========