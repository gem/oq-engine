Simple Fault Demo, Classical PSHA
=================================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           1.0      
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         20.0     
complex_fault_mesh_spacing   20.0     
width_of_mfd_bin             0.5      
area_source_discretization   20.0     
random_seed                  23       
master_seed                  0        
============================ =========

Input files
-----------
=========================== =========================================================
Name                        File                                                     
exposure                    demos/ClassicalPSHA/exposure_model.xml                   
gsim_logic_tree             demos/ClassicalPSHA/gmpe_logic_tree.xml                  
job_ini                     demos/ClassicalPSHA/job_hazard.ini                       
nonstructural_vulnerability demos/ClassicalPSHA/nonstructural_vulnerability_model.xml
occupants_vulnerability     demos/ClassicalPSHA/occupants_vulnerability_model.xml    
source                      demos/ClassicalPSHA/source_model.xml                     
source_model_logic_tree     demos/ClassicalPSHA/source_model_logic_tree.xml          
structural_vulnerability    demos/ClassicalPSHA/structural_vulnerability_model.xml   
=========================== =========================================================

Composite source model
----------------------
========= ================= ======== =============== ========= ================ ===========
smlt_path source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
========= ================= ======== =============== ========= ================ ===========
b1        source_model.xml  1        trivial         1         1/1              1364       
========= ================= ======== =============== ========= ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,ChiouYoungs2008: ['<0,b1,b1,w=1.0>']>