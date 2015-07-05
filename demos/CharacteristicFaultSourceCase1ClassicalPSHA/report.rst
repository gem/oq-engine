Classical PSHA with Characteristic Fault Source defined as sequence of planar fault segments
============================================================================================

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
======================= ==============================================================================
Name                    File                                                                          
gsim_logic_tree         /demos/CharacteristicFaultSourceCase1ClassicalPSHA/gmpe_logic_tree.xml        
job_ini                 /demos/CharacteristicFaultSourceCase1ClassicalPSHA/job.ini                    
source                  /demos/CharacteristicFaultSourceCase1ClassicalPSHA/source_model.xml           
source_model_logic_tree /demos/CharacteristicFaultSourceCase1ClassicalPSHA/source_model_logic_tree.xml
======================= ==============================================================================

Composite source model
----------------------
================= ======== =============== ========= ================ ===========
source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
================= ======== =============== ========= ================ ===========
source_model.xml  1        trivial         1         1/1              1          
================= ======== =============== ========= ================ ===========