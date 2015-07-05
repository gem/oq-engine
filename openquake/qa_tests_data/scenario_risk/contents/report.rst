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
======================== =================================================================================
Name                     File                                                                             
contents_vulnerability   /openquake/qa_tests_data/scenario_risk/contents/vulnerability_model_contents.xml 
exposure                 /openquake/qa_tests_data/scenario_risk/contents/exposure_model.xml               
job_ini                  /openquake/qa_tests_data/scenario_risk/contents/job.ini                          
rupture_model            /openquake/qa_tests_data/scenario_risk/contents/fault_rupture.xml                
structural_vulnerability /openquake/qa_tests_data/scenario_risk/contents/vulnerability_model_structure.xml
======================== =================================================================================