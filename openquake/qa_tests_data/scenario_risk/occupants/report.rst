Scenario QA Test for occupants
==============================

Parameters
----------
============================ ========
calculation_mode             scenario
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
============================ ========

Input files
-----------
======================= =================================================================================
Name                    File                                                                             
exposure                openquake/qa_tests_data/scenario_risk/occupants/exposure_model.xml               
job_ini                 openquake/qa_tests_data/scenario_risk/occupants/job_haz.ini                      
occupants_vulnerability openquake/qa_tests_data/scenario_risk/occupants/vulnerability_model_occupants.xml
rupture_model           openquake/qa_tests_data/scenario_risk/occupants/fault_rupture.xml                
======================= =================================================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <openquake.commonlib.logictree.RlzsAssoc object at 0x7f0c948e82d0>