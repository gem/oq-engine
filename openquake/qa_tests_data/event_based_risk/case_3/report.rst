Event Based PSHA for Lisbon
===========================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             400.0      
investigation_time           50.0       
ses_per_logic_tree_path      1          
truncation_level             5.0        
rupture_mesh_spacing         2.0        
complex_fault_mesh_spacing   2.0        
width_of_mfd_bin             0.1        
area_source_discretization   5.0        
random_seed                  23         
master_seed                  0          
============================ ===========

Input files
-----------
======================== ===========================================================================
Name                     File                                                                       
exposure                 openquake/qa_tests_data/event_based_risk/case_3/exposure_model_10assets.xml
gsim_logic_tree          openquake/qa_tests_data/event_based_risk/case_3/gsim_logic_tree.xml        
job_ini                  openquake/qa_tests_data/event_based_risk/case_3/job_haz.ini                
source                   openquake/qa_tests_data/event_based_risk/case_3/SA_RA_CATAL1_00.xml        
source                   openquake/qa_tests_data/event_based_risk/case_3/SA_RA_CATAL2_00.xml        
source_model_logic_tree  openquake/qa_tests_data/event_based_risk/case_3/source_model_logic_tree.xml
structural_vulnerability openquake/qa_tests_data/event_based_risk/case_3/vulnerability_model2013.xml
======================== ===========================================================================

Composite source model
----------------------
========= =================== ======== =============== ========= ================ ===========
smlt_path source_model_file   num_trts gsim_logic_tree num_gsims num_realizations num_sources
========= =================== ======== =============== ========= ================ ===========
b1        SA_RA_CATAL1_00.xml 2        complex         2,2       4/4              11         
b2        SA_RA_CATAL2_00.xml 2        complex         2,2       4/4              11         
========= =================== ======== =============== ========= ================ ===========

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b1        Active Shallow Crust 123         
1   b1        Stable Shallow Crust 43          
2   b2        Active Shallow Crust 115         
3   b2        Stable Shallow Crust 42          
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
(0, 1)      [0, 1, 2, 3]
(2, 3)      [4, 5, 6, 7]
=========== ============