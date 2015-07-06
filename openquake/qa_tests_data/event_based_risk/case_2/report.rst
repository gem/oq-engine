PEB QA test 2
=============

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             100.0      
investigation_time           50.0       
ses_per_logic_tree_path      20         
truncation_level             3.0        
rupture_mesh_spacing         5.0        
complex_fault_mesh_spacing   5.0        
width_of_mfd_bin             0.3        
area_source_discretization   10.0       
random_seed                  23         
master_seed                  0          
============================ ===========

Input files
-----------
======================== ============================================================================
Name                     File                                                                        
gsim_logic_tree          openquake/qa_tests_data/event_based_risk/case_2/gmpe_logic_tree.xml         
job_ini                  openquake/qa_tests_data/event_based_risk/case_2/job_haz.ini                 
source                   openquake/qa_tests_data/event_based_risk/case_2/source_model.xml            
source_model_logic_tree  openquake/qa_tests_data/event_based_risk/case_2/source_model_logic_tree.xml 
structural_vulnerability openquake/qa_tests_data/event_based_risk/case_2/vulnerability_model_stco.xml
======================== ============================================================================

Composite source model
----------------------
========= ================= ======== =============== ========= ================ ===========
smlt_path source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
========= ================= ======== =============== ========= ================ ===========
b1        source_model.xml  1        trivial         1         1/1              3          
========= ================= ======== =============== ========= ================ ===========

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b1        Active Shallow Crust 20          
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
(0,)        [0]         
=========== ============