Classical PSHA-Based Hazard
===========================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           1.0      
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         1.0      
complex_fault_mesh_spacing   1.0      
width_of_mfd_bin             0.1      
area_source_discretization   20.0     
random_seed                  42       
master_seed                  0        
============================ =========

Input files
-----------
======================= ====================================================
Name                    File                                                
exposure                demos/ClassicalDamage/exposure_model.xml            
fragility               demos/ClassicalDamage/structural_fragility_model.xml
gsim_logic_tree         demos/ClassicalDamage/gmpe_logic_tree.xml           
job_ini                 demos/ClassicalDamage/job_hazard.ini                
source                  demos/ClassicalDamage/source_model.xml              
source_model_logic_tree demos/ClassicalDamage/source_model_logic_tree.xml   
======================= ====================================================

Composite source model
----------------------
========= ================= ======== =============== ========= ================ ===========
smlt_path source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
========= ================= ======== =============== ========= ================ ===========
b1        source_model.xml  1        trivial         1         1/1              398        
========= ================= ======== =============== ========= ================ ===========