QA test for blocksize independence (hazard)
===========================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 1          
maximum_distance             400.0      
investigation_time           5.0        
ses_per_logic_tree_path      1          
truncation_level             3.0        
rupture_mesh_spacing         10.0       
complex_fault_mesh_spacing   10.0       
width_of_mfd_bin             0.5        
area_source_discretization   10.0       
random_seed                  1024       
master_seed                  0          
============================ ===========

Input files
-----------
======================= ==================================================================================================
Name                    File                                                                                              
gsim_logic_tree         /home/michele/oq-risklib/openquake/qa_tests_data/event_based/blocksize/gmpe_logic_tree.xml        
job_ini                 /home/michele/oq-risklib/openquake/qa_tests_data/event_based/blocksize/job.ini                    
source_model_logic_tree /home/michele/oq-risklib/openquake/qa_tests_data/event_based/blocksize/source_model_logic_tree.xml
source                  /openquake/qa_tests_data/event_based/blocksize/source_model.xml                                   
======================= ==================================================================================================

Composite source model
----------------------
================= ======== =============== ========= ================ ===========
source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
================= ======== =============== ========= ================ ===========
source_model.xml  1        trivial         1         1/1              398        
================= ======== =============== ========= ================ ===========

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
(0,)        [0]         
=========== ============