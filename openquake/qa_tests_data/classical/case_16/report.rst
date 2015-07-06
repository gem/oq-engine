Classical PSHA with non-trivial logic tree (1 source model + 5 (a, b) pairs per source + 3 Mmax per source
==========================================================================================================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 10       
maximum_distance             200.0    
investigation_time           50.0     
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         2.0      
complex_fault_mesh_spacing   2.0      
width_of_mfd_bin             0.1      
area_source_discretization   10.0     
random_seed                  23       
master_seed                  0        
============================ =========

Input files
-----------
======================= =====================================================================
Name                    File                                                                 
gsim_logic_tree         openquake/qa_tests_data/classical/case_16/gmpe_logic_tree.xml        
job_ini                 openquake/qa_tests_data/classical/case_16/job.ini                    
source                  openquake/qa_tests_data/classical/case_16/source_model.xml           
source_model_logic_tree openquake/qa_tests_data/classical/case_16/source_model_logic_tree.xml
======================= =====================================================================

Composite source model
----------------------
============================================= ================= ======== =============== ========= ================ ===========
smlt_path                                     source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
============================================= ================= ======== =============== ========= ================ ===========
b11_b20_b31_b43_b52_b62_b72_b82_b91_b103_b112 source_model.xml  1        trivial         1         1/1              135        
b11_b21_b32_b43_b52_b62_b72_b82_b92_b102_b112 source_model.xml  1        trivial         1         1/1              135        
b11_b21_b32_b43_b52_b62_b73_b82_b92_b103_b113 source_model.xml  1        trivial         1         1/1              135        
b11_b22_b31_b43_b52_b64_b73_b84_b92_b104_b112 source_model.xml  1        trivial         1         1/1              135        
b11_b22_b32_b42_b51_b61_b72_b83_b91_b101_b111 source_model.xml  1        trivial         1         1/1              135        
b11_b22_b32_b42_b53_b62_b72_b81_b92_b103_b112 source_model.xml  1        trivial         1         1/1              135        
b11_b22_b33_b42_b52_b62_b72_b82_b92_b100_b112 source_model.xml  1        trivial         1         1/1              135        
b11_b23_b32_b43_b52_b62_b73_b82_b93_b101_b113 source_model.xml  1        trivial         1         1/1              135        
b11_b24_b32_b41_b51_b62_b71_b84_b93_b101_b111 source_model.xml  1        trivial         1         1/1              135        
b11_b24_b33_b40_b52_b62_b72_b81_b91_b102_b112 source_model.xml  1        trivial         1         1/1              135        
============================================= ================= ======== =============== ========= ================ ===========