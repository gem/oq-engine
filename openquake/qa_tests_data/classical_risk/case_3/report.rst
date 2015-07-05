Classical PSHA - Loss fractions QA test
=======================================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 1        
maximum_distance             200.0    
investigation_time           50.0     
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         5.0      
complex_fault_mesh_spacing   5.0      
width_of_mfd_bin             0.2      
area_source_discretization   10.0     
random_seed                  23       
master_seed                  0        
============================ =========

Input files
-----------
======================= =========================================================================
Name                    File                                                                     
gsim_logic_tree         openquake/qa_tests_data/classical_risk/case_3/gmpe_logic_tree.xml        
job_ini                 openquake/qa_tests_data/classical_risk/case_3/job_haz.ini                
source                  openquake/qa_tests_data/classical_risk/case_3/source_model.xml           
source_model_logic_tree openquake/qa_tests_data/classical_risk/case_3/source_model_logic_tree.xml
======================= =========================================================================

Composite source model
----------------------
========= ================= ======== =============== ========= ================ ===========
smlt_path source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
========= ================= ======== =============== ========= ================ ===========
b1        source_model.xml  1        trivial         1         1/1              398        
========= ================= ======== =============== ========= ================ ===========