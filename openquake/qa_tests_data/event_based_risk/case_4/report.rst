Event Based Hazard for Turkey reduced
=====================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             200.0      
investigation_time           10.0       
ses_per_logic_tree_path      1          
truncation_level             3.0        
rupture_mesh_spacing         2.0        
complex_fault_mesh_spacing   2.0        
width_of_mfd_bin             0.1        
area_source_discretization   10.0       
random_seed                  323        
master_seed                  0          
============================ ===========

Input files
-----------
======================== ===============================================================================================
Name                     File                                                                                           
exposure                 /openquake/qa_tests_data/event_based_risk/case_4/models/exp/exposure.xml                       
gsim_logic_tree          /openquake/qa_tests_data/event_based_risk/case_4/models/tree/gmpe_logic_tree.xml               
job_ini                  /openquake/qa_tests_data/event_based_risk/case_4/job_hazard.ini                                
source                   /openquake/qa_tests_data/event_based_risk/case_4/models/src/as_model.xml                       
source                   /openquake/qa_tests_data/event_based_risk/case_4/models/src/fsbg_model.xml                     
source                   /openquake/qa_tests_data/event_based_risk/case_4/models/src/ss_model.xml                       
source_model_logic_tree  /openquake/qa_tests_data/event_based_risk/case_4/models/tree/source_model_logic_tree.xml       
structural_vulnerability /openquake/qa_tests_data/event_based_risk/case_4/models/vuln/structural_vulnerability_model.xml
======================== ===============================================================================================

Composite source model
----------------------
======================== ========================= ======== =============== ========= ================ ===========
smlt_path                source_model_file         num_trts gsim_logic_tree num_gsims num_realizations num_sources
======================== ========================= ======== =============== ========= ================ ===========
AreaSource               models/src/as_model.xml   1        complex         4         4/4              44         
FaultSourceAndBackground models/src/fsbg_model.xml 1        complex         4         4/4              110        
SeiFaCrust               models/src/ss_model.xml   0        complex                   0/0              1          
======================== ========================= ======== =============== ========= ================ ===========

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
(5,)        [0, 1, 2, 3]
(9,)        [4, 5, 6, 7]
=========== ============