Classical Hazard QA Test, Case 17
=================================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 5        
maximum_distance             200.0    
investigation_time           1000.0   
ses_per_logic_tree_path      1        
truncation_level             2.0      
rupture_mesh_spacing         1.0      
complex_fault_mesh_spacing   1.0      
width_of_mfd_bin             1.0      
area_source_discretization   10.0     
random_seed                  106      
master_seed                  0        
concurrent_tasks             64       
============================ =========

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ========================================== =============== ================ ===========
smlt_path weight source_model_file                          gsim_logic_tree num_realizations num_sources
========= ====== ========================================== =============== ================ ===========
b1        0.2    `source_model_1.xml <source_model_1.xml>`_ trivial(1)      1/1              1          
b2        0.2    `source_model_2.xml <source_model_2.xml>`_ trivial(1)      4/1              1          
========= ====== ========================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(2)
  0,SadighEtAl1997: ['<0,b1,b1,w=0.2>']
  1,SadighEtAl1997: ['<1,b2,b1,w=0.2>', '<2,b2,b1,w=0.2>', '<3,b2,b1,w=0.2>', '<4,b2,b1,w=0.2>']>

Number of ruptures per tectonic region type
-------------------------------------------
=========== ==
#TRT models 2 
#sources    2 
#ruptures   46
=========== ==

================== ====== ==================== =========== ============
source_model       trt_id trt                  num_sources num_ruptures
================== ====== ==================== =========== ============
source_model_1.xml 0      active shallow crust 1           39          
source_model_2.xml 1      active shallow crust 1           7           
================== ====== ==================== =========== ============

Expected data transfer for the sources
--------------------------------------
================================== =======
Number of tasks to generate        2      
Estimated sources to send          4.07 KB
Estimated hazard curves to receive 48 B   
================================== =======