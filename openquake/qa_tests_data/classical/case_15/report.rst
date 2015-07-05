Classical PSHA with GMPE logic tree with multiple tectonic region types
=======================================================================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           50.0     
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         1.0      
complex_fault_mesh_spacing   1.0      
width_of_mfd_bin             0.1      
area_source_discretization   10.0     
random_seed                  23       
master_seed                  0        
============================ =========

Input files
-----------
======================= ==============================================================================================
Name                    File                                                                                          
gsim_logic_tree         /home/michele/oq-risklib/openquake/qa_tests_data/classical/case_15/gmpe_logic_tree.xml        
job_ini                 /home/michele/oq-risklib/openquake/qa_tests_data/classical/case_15/job.ini                    
source_model_logic_tree /home/michele/oq-risklib/openquake/qa_tests_data/classical/case_15/source_model_logic_tree.xml
source                  /openquake/qa_tests_data/classical/case_15/source_model_1.xml                                 
source                  /openquake/qa_tests_data/classical/case_15/source_model_2.xml                                 
======================= ==============================================================================================

Composite source model
----------------------
================== ======== =============== ========= ================ ===========
source_model_file  num_trts gsim_logic_tree num_gsims num_realizations num_sources
================== ======== =============== ========= ================ ===========
source_model_1.xml 2        complex         2,2       4/4              2          
source_model_2.xml 1        complex         2         2/2              1          
source_model_2.xml 1        complex         2         2/2              1          
================== ======== =============== ========= ================ ===========