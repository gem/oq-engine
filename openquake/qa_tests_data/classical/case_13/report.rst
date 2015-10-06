Classical PSHA QA test
======================

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
concurrent_tasks             64       
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
========================= ====== ================================================================ =============== ================ ===========
smlt_path                 weight source_model_file                                                gsim_logic_tree num_realizations num_sources
========================= ====== ================================================================ =============== ================ ===========
aFault_aPriori_D2.1       0.50   `aFault_aPriori_D2.1.xml <aFault_aPriori_D2.1.xml>`_             simple(2)       2/2              168        
bFault_stitched_D2.1_Char 0.50   `bFault_stitched_D2.1_Char.xml <bFault_stitched_D2.1_Char.xml>`_ simple(2)       2/2              186        
========================= ====== ================================================================ =============== ================ ===========

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
=========== ====
#TRT models 2   
#sources    354 
#ruptures   3894
=========== ====

============================= ====== ==================== =========== ============
source_model                  trt_id trt                  num_sources num_ruptures
============================= ====== ==================== =========== ============
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 168         1848        
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 186         2046        
============================= ====== ==================== =========== ============

Expected data transfer for the sources
--------------------------------------
================================== =======
Number of tasks to generate        72     
Estimated sources to send          1.36 MB
Estimated hazard curves to receive 614 KB 
================================== =======