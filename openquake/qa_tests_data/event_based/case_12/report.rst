Event Based QA Test, Case 12
============================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             200.0      
investigation_time           1.0        
ses_per_logic_tree_path      3500       
truncation_level             2.0        
rupture_mesh_spacing         1.0        
complex_fault_mesh_spacing   1.0        
width_of_mfd_bin             1.0        
area_source_discretization   10.0       
random_seed                  1066       
master_seed                  0          
============================ ===========

Input files
-----------
======================= =======================================================================
Name                    File                                                                   
======================= =======================================================================
gsim_logic_tree         openquake/qa_tests_data/event_based/case_12/gsim_logic_tree.xml        
job_ini                 openquake/qa_tests_data/event_based/case_12/job.ini                    
source                  openquake/qa_tests_data/event_based/case_12/source_model.xml           
source_model_logic_tree openquake/qa_tests_data/event_based/case_12/source_model_logic_tree.xml
======================= =======================================================================

Composite source model
----------------------
========= ================= ======== =============== ========= ================ ===========
smlt_path source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
========= ================= ======== =============== ========= ================ ===========
b1        source_model.xml  2        trivial         1,1       1/1              2          
========= ================= ======== =============== ========= ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(2)
  0,SadighEtAl1997: ['<0,b1,b1_b2,w=1.0>']
  1,BooreAtkinson2008: ['<0,b1,b1_b2,w=1.0>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b1        active shallow crust 3420        
1   b1        stable continental   3346        
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
(0, 1)      [0]         
=========== ============