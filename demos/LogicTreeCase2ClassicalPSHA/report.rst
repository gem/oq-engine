Classical PSHA with non-trivial logic tree (1 source model + absolute uncertainties on G-R a and b values and maximum magnitude and 2 GMPEs per tectonic region type)
=====================================================================================================================================================================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           50.0     
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         2.0      
complex_fault_mesh_spacing   2.0      
width_of_mfd_bin             0.1      
area_source_discretization   5.0      
random_seed                  23       
master_seed                  0        
============================ =========

Input files
-----------
======================= =============================================================
Name                    File                                                         
gsim_logic_tree         demos/LogicTreeCase2ClassicalPSHA/gmpe_logic_tree.xml        
job_ini                 demos/LogicTreeCase2ClassicalPSHA/job.ini                    
source                  demos/LogicTreeCase2ClassicalPSHA/source_model.xml           
source_model_logic_tree demos/LogicTreeCase2ClassicalPSHA/source_model_logic_tree.xml
======================= =============================================================

Composite source model
----------------------
=================== ================= ======== =============== ========= ================ ===========
smlt_path           source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
=================== ================= ======== =============== ========= ================ ===========
b11_b21_b31_b41_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b31_b41_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b31_b41_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b31_b42_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b31_b42_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b31_b42_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b31_b43_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b31_b43_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b31_b43_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b32_b41_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b32_b41_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b32_b41_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b32_b42_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b32_b42_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b32_b42_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b32_b43_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b32_b43_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b32_b43_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b33_b41_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b33_b41_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b33_b41_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b33_b42_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b33_b42_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b33_b42_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b33_b43_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b33_b43_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b21_b33_b43_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b31_b41_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b31_b41_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b31_b41_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b31_b42_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b31_b42_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b31_b42_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b31_b43_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b31_b43_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b31_b43_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b32_b41_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b32_b41_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b32_b41_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b32_b42_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b32_b42_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b32_b42_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b32_b43_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b32_b43_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b32_b43_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b33_b41_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b33_b41_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b33_b41_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b33_b42_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b33_b42_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b33_b42_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b33_b43_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b33_b43_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b22_b33_b43_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b31_b41_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b31_b41_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b31_b41_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b31_b42_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b31_b42_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b31_b42_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b31_b43_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b31_b43_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b31_b43_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b32_b41_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b32_b41_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b32_b41_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b32_b42_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b32_b42_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b32_b42_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b32_b43_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b32_b43_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b32_b43_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b33_b41_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b33_b41_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b33_b41_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b33_b42_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b33_b42_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b33_b42_b53 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b33_b43_b51 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b33_b43_b52 source_model.xml  2        complex         2,2       4/4              2          
b11_b23_b33_b43_b53 source_model.xml  2        complex         2,2       4/4              2          
=================== ================= ======== =============== ========= ================ ===========