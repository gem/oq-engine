Classical Hazard QA Test, Case 12
=================================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           1.0      
ses_per_logic_tree_path      1        
truncation_level             2.0      
rupture_mesh_spacing         1.0      
complex_fault_mesh_spacing   1.0      
width_of_mfd_bin             1.0      
area_source_discretization   10.0     
random_seed                  1066     
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
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================ ===========
smlt_path weight source_model_file                      gsim_logic_tree num_realizations num_sources
========= ====== ====================================== =============== ================ ===========
b1        1.00   `source_model.xml <source_model.xml>`_ trivial(1,1)    1/1              2          
========= ====== ====================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(2)
  0,SadighEtAl1997: ['<0,b1,b1_b2,w=1.0>']
  1,BooreAtkinson2008: ['<0,b1,b1_b2,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
=========== =
#TRT models 2
#sources    2
#ruptures   2
=========== =

================ ====== ==================== =========== ============
source_model     trt_id trt                  num_sources num_ruptures
================ ====== ==================== =========== ============
source_model.xml 0      active shallow crust 1           1           
source_model.xml 1      stable continental   1           1           
================ ====== ==================== =========== ============

Expected data transfer for the sources
--------------------------------------
================================== =======
Number of tasks to generate        2      
Estimated sources to send          3.92 KB
Estimated hazard curves to receive 48 B   
================================== =======