Event Based QA Test, Case 13
============================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             200.0      
investigation_time           1.0        
ses_per_logic_tree_path      5000       
truncation_level             2.0        
rupture_mesh_spacing         1.0        
complex_fault_mesh_spacing   1.0        
width_of_mfd_bin             1.0        
area_source_discretization   10.0       
random_seed                  1066       
master_seed                  0          
============================ ===========

Input files
-----------
======================= ================================================================================================
Name                    File                                                                                            
gsim_logic_tree         /home/michele/oq-risklib/openquake/qa_tests_data/event_based/case_13/gsim_logic_tree.xml        
job_ini                 /home/michele/oq-risklib/openquake/qa_tests_data/event_based/case_13/job.ini                    
source_model_logic_tree /home/michele/oq-risklib/openquake/qa_tests_data/event_based/case_13/source_model_logic_tree.xml
source                  /openquake/qa_tests_data/event_based/case_13/source_model.xml                                   
======================= ================================================================================================

Composite source model
----------------------
================= ======== =============== ========= ================ ===========
source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
================= ======== =============== ========= ================ ===========
source_model.xml  1        trivial         1         1/1              1          
================= ======== =============== ========= ================ ===========

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
(0,)        [0]         
=========== ============