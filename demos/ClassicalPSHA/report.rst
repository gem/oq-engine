Simple Fault Demo, Classical PSHA
=================================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           1.0      
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         20.0     
complex_fault_mesh_spacing   20.0     
width_of_mfd_bin             0.5      
area_source_discretization   20.0     
random_seed                  23       
master_seed                  0        
============================ =========

Input files
-----------
=========================== ================================================================================
Name                        File                                                                            
=========================== ================================================================================
exposure                    `exposure_model.xml <exposure_model.xml>`_                                      
gsim_logic_tree             `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                                    
job_ini                     `job_hazard.ini <job_hazard.ini>`_                                              
nonstructural_vulnerability `nonstructural_vulnerability_model.xml <nonstructural_vulnerability_model.xml>`_
occupants_vulnerability     `occupants_vulnerability_model.xml <occupants_vulnerability_model.xml>`_        
source                      `source_model.xml <source_model.xml>`_                                          
source_model_logic_tree     `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                    
structural_vulnerability    `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_      
=========================== ================================================================================

Composite source model
----------------------
========= ================= ======== =============== ========= ================ ===========
smlt_path source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
========= ================= ======== =============== ========= ================ ===========
b1        source_model.xml  1        trivial         1         1/1              1364       
========= ================= ======== =============== ========= ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,ChiouYoungs2008: ['<0,b1,b1,w=1.0>']>