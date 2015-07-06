Scenario Calculation with Simple Fault Rupture
==============================================

Parameters
----------
============================ ========
calculation_mode             scenario
number_of_logic_tree_samples 0       
maximum_distance             200.0   
investigation_time           None    
ses_per_logic_tree_path      1       
truncation_level             3.0     
rupture_mesh_spacing         2.0     
complex_fault_mesh_spacing   2.0     
width_of_mfd_bin             None    
area_source_discretization   None    
random_seed                  42      
master_seed                  0       
============================ ========

Input files
-----------
============= ===============================================================
Name          File                                                           
job_ini       openquake/qa_tests_data/scenario_risk/case_1g/job_haz.ini      
rupture_model openquake/qa_tests_data/scenario_risk/case_1g/rupture_model.xml
sites         openquake/qa_tests_data/scenario_risk/case_1g/sites.csv        
============= ===============================================================