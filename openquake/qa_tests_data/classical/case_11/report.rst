Classical Hazard QA Test, Case 11
=================================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           1.0      
ses_per_logic_tree_path      1        
truncation_level             0.0      
rupture_mesh_spacing         0.01     
complex_fault_mesh_spacing   0.01     
width_of_mfd_bin             0.001    
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
b1_b2     0.200  `source_model.xml <source_model.xml>`_ trivial(1)      1/1              1          
b1_b3     0.600  `source_model.xml <source_model.xml>`_ trivial(1)      1/1              1          
b1_b4     0.200  `source_model.xml <source_model.xml>`_ trivial(1)      1/1              1          
========= ====== ====================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(3)
  0,SadighEtAl1997: ['<0,b1_b2,b1,w=0.2>']
  1,SadighEtAl1997: ['<1,b1_b3,b1,w=0.6>']
  2,SadighEtAl1997: ['<2,b1_b4,b1,w=0.2>']>

Number of ruptures per tectonic region type
-------------------------------------------
=========== ====
#TRT models 3   
#sources    3   
#ruptures   9000
=========== ====

================ ====== ==================== =========== ============
source_model     trt_id trt                  num_sources num_ruptures
================ ====== ==================== =========== ============
source_model.xml 0      active shallow crust 1           3500        
source_model.xml 1      active shallow crust 1           3000        
source_model.xml 2      active shallow crust 1           2500        
================ ====== ==================== =========== ============

Expected data transfer for the sources
--------------------------------------
================================== =======
Number of tasks to generate        3      
Estimated sources to send          5.79 KB
Estimated hazard curves to receive 96 B   
================================== =======