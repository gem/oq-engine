Germany_SHARE Combined Model event_based
========================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             80.0       
investigation_time           30.0       
ses_per_logic_tree_path      1          
truncation_level             3.0        
rupture_mesh_spacing         5.0        
complex_fault_mesh_spacing   5.0        
width_of_mfd_bin             0.1        
area_source_discretization   10.0       
random_seed                  23         
master_seed                  0          
============================ ===========

Input files
-----------
======================= ========================================================================================================
Name                    File                                                                                                    
gsim_logic_tree         /home/michele/oq-risklib/openquake/qa_tests_data/event_based/case_5/complete_gmpe_logic_tree.xml        
job_ini                 /home/michele/oq-risklib/openquake/qa_tests_data/event_based/case_5/job.ini                             
sites                   /home/michele/oq-risklib/openquake/qa_tests_data/event_based/case_5/sites.csv                           
source_model_logic_tree /home/michele/oq-risklib/openquake/qa_tests_data/event_based/case_5/combined_logic-tree-source-model.xml
source                  /openquake/qa_tests_data/event_based/case_5/source_models/as_model.xml                                  
source                  /openquake/qa_tests_data/event_based/case_5/source_models/fs_bg_source_model.xml                        
source                  /openquake/qa_tests_data/event_based/case_5/source_models/ss_model_final_250km_Buffer.xml               
======================= ========================================================================================================

Composite source model
----------------------
============================================= ======== =============== ========= ================ ===========
source_model_file                             num_trts gsim_logic_tree num_gsims num_realizations num_sources
============================================= ======== =============== ========= ================ ===========
source_models/as_model.xml                    0        complex                   0/0              6          
source_models/fs_bg_source_model.xml          1        complex         5         5/5              85         
source_models/ss_model_final_250km_Buffer.xml 1        complex         1         1/1              51         
============================================= ======== =============== ========= ================ ===========

Collections <-> realizations
----------------------------
=========== ===============
Collections Realizations   
(4,)        [0, 1, 2, 3, 4]
(7,)        [5]            
=========== ===============