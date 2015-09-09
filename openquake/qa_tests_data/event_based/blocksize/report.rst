QA test for blocksize independence (hazard)
===========================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 1          
maximum_distance             400.0      
investigation_time           5.0        
ses_per_logic_tree_path      1          
truncation_level             3.0        
rupture_mesh_spacing         10.0       
complex_fault_mesh_spacing   10.0       
width_of_mfd_bin             0.5        
area_source_discretization   10.0       
random_seed                  1024       
master_seed                  0          
concurrent_tasks             32         
============================ ===========

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================ ===========
smlt_path weight source_model_file                      gsim_logic_tree num_realizations num_sources
========= ====== ====================================== =============== ================ ===========
b1        1.0    `source_model.xml <source_model.xml>`_ trivial(1)      1/1              4168       
========= ====== ====================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,ChiouYoungs2008: ['<0,b1,b1,w=1.0>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b1        Active Shallow Crust 4           
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
0           0           
=========== ============

Expected data transfer for the sources
--------------------------------------
================================== =========
Number of tasks to generate        32       
Estimated sources to send          990.89 KB
Estimated hazard curves to receive 2 KB     
================================== =========