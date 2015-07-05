Event Based Hazard
==================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             200.0      
investigation_time           1.0        
ses_per_logic_tree_path      100        
truncation_level             3.0        
rupture_mesh_spacing         2.0        
complex_fault_mesh_spacing   2.0        
width_of_mfd_bin             0.1        
area_source_discretization   10.0       
random_seed                  24         
master_seed                  0          
============================ ===========

Input files
-----------
======================== ====================================================================================
Name                     File                                                                                
exposure                 /openquake/qa_tests_data/event_based_risk/case_4a/exposure_model.xml                
gsim_logic_tree          /openquake/qa_tests_data/event_based_risk/case_4a/gmpe_logic_tree.xml               
job_ini                  /openquake/qa_tests_data/event_based_risk/case_4a/job_hazard.ini                    
site_model               /openquake/qa_tests_data/event_based_risk/case_4a/site_model.xml                    
source                   /openquake/qa_tests_data/event_based_risk/case_4a/source_model.xml                  
source_model_logic_tree  /openquake/qa_tests_data/event_based_risk/case_4a/source_model_logic_tree.xml       
structural_vulnerability /openquake/qa_tests_data/event_based_risk/case_4a/structural_vulnerability_model.xml
======================== ====================================================================================

Composite source model
----------------------
========= ================= ======== =============== ========= ================ ===========
smlt_path source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
========= ================= ======== =============== ========= ================ ===========
b1        source_model.xml  1        trivial         1         1/1              2          
========= ================= ======== =============== ========= ================ ===========

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
(0,)        [0]         
=========== ============