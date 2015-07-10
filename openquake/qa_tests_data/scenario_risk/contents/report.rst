QA Scenario Risk for contents
=============================

Parameters
----------
============================ =============
calculation_mode             scenario_risk
number_of_logic_tree_samples 0            
maximum_distance             300.0        
investigation_time           None         
ses_per_logic_tree_path      1            
truncation_level             3.0          
rupture_mesh_spacing         10.0         
complex_fault_mesh_spacing   10.0         
width_of_mfd_bin             None         
area_source_discretization   None         
random_seed                  3            
master_seed                  0            
============================ =============

Input files
-----------
======================== ========================================================================
Name                     File                                                                    
======================== ========================================================================
contents_vulnerability   `vulnerability_model_contents.xml <vulnerability_model_contents.xml>`_  
exposure                 `exposure_model.xml <exposure_model.xml>`_                              
job_ini                  `job.ini <job.ini>`_                                                    
rupture_model            `fault_rupture.xml <fault_rupture.xml>`_                                
structural_vulnerability `vulnerability_model_structure.xml <vulnerability_model_structure.xml>`_
======================== ========================================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,ChiouYoungs2008: ['ChiouYoungs2008']>