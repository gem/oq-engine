Event-Based Hazard QA Test, Case 18
===================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 3          
maximum_distance             200.0      
investigation_time           1.0        
ses_per_logic_tree_path      350        
truncation_level             0.0        
rupture_mesh_spacing         1.0        
complex_fault_mesh_spacing   1.0        
width_of_mfd_bin             0.001      
area_source_discretization   10.0       
random_seed                  1064       
master_seed                  0          
============================ ===========

Input files
-----------
======================= =======================================================================
Name                    File                                                                   
gsim_logic_tree         openquake/qa_tests_data/event_based/case_18/three_gsim_logic_tree.xml  
job_ini                 openquake/qa_tests_data/event_based/case_18/job.ini                    
source                  openquake/qa_tests_data/event_based/case_18/source_model.xml           
source_model_logic_tree openquake/qa_tests_data/event_based/case_18/source_model_logic_tree.xml
======================= =======================================================================

Composite source model
----------------------
========= ================= ======== =============== ========= ================ ===========
smlt_path source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
========= ================= ======== =============== ========= ================ ===========
b1        source_model.xml  1        simple          3         3/3              1          
========= ================= ======== =============== ========= ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(2)
  0,AkkarBommer2010: ['<0,b1,AB,w=0.333333333333,col=0>', '<1,b1,AB,w=0.333333333333,col=1>']
  0,CauzziFaccioli2008: ['<2,b1,CF,w=0.333333333333,col=2>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b1        active shallow crust 3           
1   b1        active shallow crust 5           
2   b1        active shallow crust 5           
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
(0,)        [0]         
(1,)        [1]         
(2,)        [2]         
=========== ============