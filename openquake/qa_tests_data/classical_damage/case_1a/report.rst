Classical PSHA-Based Hazard
===========================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           1.0      
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         1.0      
complex_fault_mesh_spacing   1.0      
width_of_mfd_bin             0.1      
area_source_discretization   20.0     
random_seed                  42       
master_seed                  0        
concurrent_tasks             64       
============================ =========

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
fragility               `fragility_model.xml <fragility_model.xml>`_                
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job_haz.ini <job_haz.ini>`_                                
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================ ===========
smlt_path weight source_model_file                      gsim_logic_tree num_realizations num_sources
========= ====== ====================================== =============== ================ ===========
b1        1.00   `source_model.xml <source_model.xml>`_ trivial(1)      1/1              15         
========= ====== ====================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,SadighEtAl1997: ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============
source_model     trt_id trt                  num_sources num_ruptures
================ ====== ==================== =========== ============
source_model.xml 0      Active Shallow Crust 15          1694        
================ ====== ==================== =========== ============

Expected data transfer for the sources
--------------------------------------
================================== ========
Number of tasks to generate        14      
Estimated sources to send          25.32 KB
Estimated hazard curves to receive 896 B   
================================== ========

Exposure model
--------------
=========== =
#assets     1
#sites      1
#taxonomies 1
=========== =

======== =======
Taxonomy #Assets
======== =======
Wood     1      
======== =======