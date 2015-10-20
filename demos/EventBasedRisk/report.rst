Probabilistic Event-Based Hazard Demo
=====================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             200.0      
investigation_time           50.0       
ses_per_logic_tree_path      200        
truncation_level             3.0        
rupture_mesh_spacing         10.0       
complex_fault_mesh_spacing   10.0       
width_of_mfd_bin             0.5        
area_source_discretization   10.0       
random_seed                  1024       
master_seed                  0          
============================ ===========

Input files
-----------
=========================== ================================================================================
Name                        File                                                                            
=========================== ================================================================================
exposure                    `exposure_model.xml <exposure_model.xml>`_                                      
gsim_logic_tree             `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                                    
job_ini                     `job_hazard.ini <job_hazard.ini>`_                                              
nonstructural_vulnerability `nonstructural_vulnerability_model.xml <nonstructural_vulnerability_model.xml>`_
source                      `source_model.xml <source_model.xml>`_                                          
source_model_logic_tree     `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                    
structural_vulnerability    `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_      
=========================== ================================================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================ ===========
smlt_path weight source_model_file                      gsim_logic_tree num_realizations num_sources
========= ====== ====================================== =============== ================ ===========
b1        1.00   `source_model.xml <source_model.xml>`_ trivial(1)      1/1              5601       
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
0   b1        Active Shallow Crust 21222       
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
(0,)        [0]         
=========== ============