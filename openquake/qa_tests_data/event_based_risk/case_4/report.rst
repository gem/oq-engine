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
======================== ==============================================================================================
Name                     File                                                                                          
exposure                 openquake/qa_tests_data/event_based_risk/case_4/models/exp/exposure.xml                       
gsim_logic_tree          openquake/qa_tests_data/event_based_risk/case_4/models/tree/gmpe_logic_tree.xml               
job_ini                  openquake/qa_tests_data/event_based_risk/case_4/job_hazard.ini                                
source                   openquake/qa_tests_data/event_based_risk/case_4/models/src/as_model.xml                       
source                   openquake/qa_tests_data/event_based_risk/case_4/models/src/fsbg_model.xml                     
source                   openquake/qa_tests_data/event_based_risk/case_4/models/src/ss_model.xml                       
source_model_logic_tree  openquake/qa_tests_data/event_based_risk/case_4/models/tree/source_model_logic_tree.xml       
structural_vulnerability openquake/qa_tests_data/event_based_risk/case_4/models/vuln/structural_vulnerability_model.xml
======================== ==============================================================================================

Composite source model
----------------------
======================== ========================= ======== =============== ========= ================ ===========
smlt_path                source_model_file         num_trts gsim_logic_tree num_gsims num_realizations num_sources
======================== ========================= ======== =============== ========= ================ ===========
AreaSource               models/src/as_model.xml   1        complex         4         4/4              1319       
FaultSourceAndBackground models/src/fsbg_model.xml 1        complex         4         4/4              7060       
SeiFaCrust               models/src/ss_model.xml   0        complex                   0/0              0          
======================== ========================= ======== =============== ========= ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(8)
  5,AkkarBommer2010: ['<0,AreaSource,AkkarBommer2010asc_@_@_@_@_@_@,w=0.25>']
  5,CauzziFaccioli2008: ['<1,AreaSource,CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.25>']
  5,ChiouYoungs2008: ['<2,AreaSource,ChiouYoungs2008asc_@_@_@_@_@_@,w=0.142857142857>']
  5,ZhaoEtAl2006Asc: ['<3,AreaSource,ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.0714285714286>']
  9,AkkarBommer2010: ['<4,FaultSourceAndBackground,AkkarBommer2010asc_@_@_@_@_@_@,w=0.1>']
  9,CauzziFaccioli2008: ['<5,FaultSourceAndBackground,CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.1>']
  9,ChiouYoungs2008: ['<6,FaultSourceAndBackground,ChiouYoungs2008asc_@_@_@_@_@_@,w=0.0571428571429>']
  9,ZhaoEtAl2006Asc: ['<7,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.0285714285714>']>

Non-empty rupture collections
-----------------------------
=== ======================== ==================== ============
col smlt_path                TRT                  num_ruptures
=== ======================== ==================== ============
5   AreaSource               Active Shallow Crust 24          
9   FaultSourceAndBackground Active Shallow Crust 13          
=== ======================== ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
(5,)        [0, 1, 2, 3]
(9,)        [4, 5, 6, 7]
=========== ============