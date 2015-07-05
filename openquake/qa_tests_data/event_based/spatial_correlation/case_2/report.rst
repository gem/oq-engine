Probabilistic Event-Based QA Test with Spatial Correlation, case 2
==================================================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             200.0      
investigation_time           50.0       
ses_per_logic_tree_path      150        
truncation_level             None       
rupture_mesh_spacing         2.0        
complex_fault_mesh_spacing   2.0        
width_of_mfd_bin             0.1        
area_source_discretization   10.0       
random_seed                  123456789  
master_seed                  0          
============================ ===========

Input files
-----------
======================= ==========================================================================================
Name                    File                                                                                      
gsim_logic_tree         openquake/qa_tests_data/event_based/spatial_correlation/case_2/gmpe_logic_tree.xml        
job_ini                 openquake/qa_tests_data/event_based/spatial_correlation/case_2/job.ini                    
source                  openquake/qa_tests_data/event_based/spatial_correlation/case_2/source_model.xml           
source_model_logic_tree openquake/qa_tests_data/event_based/spatial_correlation/case_2/source_model_logic_tree.xml
======================= ==========================================================================================

Composite source model
----------------------
========= ================= ======== =============== ========= ================ ===========
smlt_path source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
========= ================= ======== =============== ========= ================ ===========
b1        source_model.xml  1        trivial         1         1/1              1          
========= ================= ======== =============== ========= ================ ===========

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b1        Active Shallow Crust 22331       
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
(0,)        [0]         
=========== ============