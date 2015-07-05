Probabilistic Event-Based QA Test with Spatial Correlation, case 1
==================================================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             200.0      
investigation_time           50.0       
ses_per_logic_tree_path      125        
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
======================= ===================================================================================================================
Name                    File                                                                                                               
gsim_logic_tree         /home/michele/oq-risklib/openquake/qa_tests_data/event_based/spatial_correlation/case_1/gmpe_logic_tree.xml        
job_ini                 /home/michele/oq-risklib/openquake/qa_tests_data/event_based/spatial_correlation/case_1/job.ini                    
source_model_logic_tree /home/michele/oq-risklib/openquake/qa_tests_data/event_based/spatial_correlation/case_1/source_model_logic_tree.xml
source                  /openquake/qa_tests_data/event_based/spatial_correlation/case_1/source_model.xml                                   
======================= ===================================================================================================================

Composite source model
----------------------
================= ======== =============== ========= ================ ===========
source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
================= ======== =============== ========= ================ ===========
source_model.xml  1        trivial         1         1/1              1          
================= ======== =============== ========= ================ ===========

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
(0,)        [0]         
=========== ============