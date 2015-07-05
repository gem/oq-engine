Classical Hazard QA Test, Case 7
================================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           1.0      
ses_per_logic_tree_path      1        
truncation_level             0.0      
rupture_mesh_spacing         0.01     
complex_fault_mesh_spacing   0.01     
width_of_mfd_bin             1.0      
area_source_discretization   10.0     
random_seed                  1066     
master_seed                  0        
============================ =========

Input files
-----------
======================= =====================================================================
Name                    File                                                                 
gsim_logic_tree         /openquake/qa_tests_data/classical/case_7/gsim_logic_tree.xml        
job_ini                 /openquake/qa_tests_data/classical/case_7/job.ini                    
source                  /openquake/qa_tests_data/classical/case_7/source_model_1.xml         
source                  /openquake/qa_tests_data/classical/case_7/source_model_2.xml         
source_model_logic_tree /openquake/qa_tests_data/classical/case_7/source_model_logic_tree.xml
======================= =====================================================================

Composite source model
----------------------
========= ================== ======== =============== ========= ================ ===========
smlt_path source_model_file  num_trts gsim_logic_tree num_gsims num_realizations num_sources
========= ================== ======== =============== ========= ================ ===========
b1        source_model_1.xml 1        trivial         1         1/1              2          
b2        source_model_2.xml 1        trivial         1         1/1              1          
========= ================== ======== =============== ========= ================ ===========