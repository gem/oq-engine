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
concurrent_tasks             32       
============================ =========

Input files
-----------
======================= ==================================================================
Name                    File                                                              
======================= ==================================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                        
fragility               `structural_fragility_model.xml <structural_fragility_model.xml>`_
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                      
job_ini                 `job_hazard.ini <job_hazard.ini>`_                                
source                  `source_model.xml <source_model.xml>`_                            
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_      
======================= ==================================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================ ===========
smlt_path weight source_model_file                      gsim_logic_tree num_realizations num_sources
========= ====== ====================================== =============== ================ ===========
b1        1.00   `source_model.xml <source_model.xml>`_ trivial(1)      1/1              1401       
========= ====== ====================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,ChiouYoungs2008: ['<0,b1,b1,w=1.0>']>

Expected data transfer for the sources
--------------------------------------
================================== =======
Number of tasks to generate        32     
Estimated sources to send          2.02 MB
Estimated hazard curves to receive 4 MB   
================================== =======