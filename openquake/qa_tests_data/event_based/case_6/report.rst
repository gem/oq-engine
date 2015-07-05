Event-based PSHA producing hazard curves only
=============================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             200.0      
investigation_time           50.0       
ses_per_logic_tree_path      300        
truncation_level             3.0        
rupture_mesh_spacing         2.0        
complex_fault_mesh_spacing   2.0        
width_of_mfd_bin             0.2        
area_source_discretization   20.0       
random_seed                  23         
master_seed                  0          
============================ ===========

Input files
-----------
======================= ===============================================================================================
Name                    File                                                                                           
gsim_logic_tree         /home/michele/oq-risklib/openquake/qa_tests_data/event_based/case_6/gmpe_logic_tree.xml        
job_ini                 /home/michele/oq-risklib/openquake/qa_tests_data/event_based/case_6/job.ini                    
source_model_logic_tree /home/michele/oq-risklib/openquake/qa_tests_data/event_based/case_6/source_model_logic_tree.xml
source                  /openquake/qa_tests_data/event_based/case_6/source_model1.xml                                  
source                  /openquake/qa_tests_data/event_based/case_6/source_model2.xml                                  
======================= ===============================================================================================

Composite source model
----------------------
================= ======== =============== ========= ================ ===========
source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
================= ======== =============== ========= ================ ===========
source_model1.xml 1        simple          3         3/3              1          
source_model2.xml 1        simple          3         3/3              1          
================= ======== =============== ========= ================ ===========

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
(0,)        [0, 1, 2]   
(1,)        [3, 4, 5]   
=========== ============