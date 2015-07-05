Event Based Hazard QA Test, Case 17
===================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 5          
maximum_distance             200.0      
investigation_time           1000.0     
ses_per_logic_tree_path      3          
truncation_level             2.0        
rupture_mesh_spacing         1.0        
complex_fault_mesh_spacing   1.0        
width_of_mfd_bin             1.0        
area_source_discretization   10.0       
random_seed                  106        
master_seed                  0          
============================ ===========

Input files
-----------
======================= ========================================================================
Name                    File                                                                    
gsim_logic_tree         /openquake/qa_tests_data/event_based/case_17/gsim_logic_tree.xml        
job_ini                 /openquake/qa_tests_data/event_based/case_17/job.ini                    
source                  /openquake/qa_tests_data/event_based/case_17/source_model_1.xml         
source                  /openquake/qa_tests_data/event_based/case_17/source_model_2.xml         
source_model_logic_tree /openquake/qa_tests_data/event_based/case_17/source_model_logic_tree.xml
======================= ========================================================================

Composite source model
----------------------
========= ================== ======== =============== ========= ================ ===========
smlt_path source_model_file  num_trts gsim_logic_tree num_gsims num_realizations num_sources
========= ================== ======== =============== ========= ================ ===========
b1        source_model_1.xml 0        trivial                   1/0              1          
b2        source_model_2.xml 1        trivial         1         4/1              1          
========= ================== ======== =============== ========= ================ ===========

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
()          [0]         
(1,)        [1]         
(2,)        [2]         
(3,)        [3]         
(4,)        [4]         
=========== ============