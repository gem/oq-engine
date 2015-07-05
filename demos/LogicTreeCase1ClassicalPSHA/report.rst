Classical PSHA with non-trivial logic tree (2 source models and 2 GMPEs per tectonic region type)
=================================================================================================

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
gsim_logic_tree         demos/LogicTreeCase1ClassicalPSHA/gmpe_logic_tree.xml        
job_ini                 demos/LogicTreeCase1ClassicalPSHA/job.ini                    
source                  demos/LogicTreeCase1ClassicalPSHA/source_model_1.xml         
source                  demos/LogicTreeCase1ClassicalPSHA/source_model_2.xml         
source_model_logic_tree demos/LogicTreeCase1ClassicalPSHA/source_model_logic_tree.xml
======================= =============================================================

Composite source model
----------------------
========= ================== ======== =============== ========= ================ ===========
smlt_path source_model_file  num_trts gsim_logic_tree num_gsims num_realizations num_sources
========= ================== ======== =============== ========= ================ ===========
b1        source_model_1.xml 2        complex         2,2       4/4              2          
b2        source_model_2.xml 2        complex         2,2       4/4              2          
========= ================== ======== =============== ========= ================ ===========