Scenario Damage QA Test 4
=========================

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
============= ==================================================================
Name          File                                                              
exposure      openquake/qa_tests_data/scenario_damage/case_4/exposure_model.xml 
fragility     openquake/qa_tests_data/scenario_damage/case_4/fragility_model.xml
job_ini       openquake/qa_tests_data/scenario_damage/case_4/job_haz.ini        
rupture_model openquake/qa_tests_data/scenario_damage/case_4/fault_rupture.xml  
============= ==================================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <openquake.commonlib.logictree.RlzsAssoc object at 0x7fdc92970fd0>