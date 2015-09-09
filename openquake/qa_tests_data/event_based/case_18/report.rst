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
concurrent_tasks             32         
============================ ===========

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `three_gsim_logic_tree.xml <three_gsim_logic_tree.xml>`_    
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ============== ====================================== =============== ================ ===========
smlt_path weight         source_model_file                      gsim_logic_tree num_realizations num_sources
========= ============== ====================================== =============== ================ ===========
b1        0.333333333333 `source_model.xml <source_model.xml>`_ simple(3)       3/3              1          
========= ============== ====================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(2)
  0,AkkarBommer2010: ['<0,b1,AB,w=0.333333333333>', '<1,b1,AB,w=0.333333333333>']
  0,CauzziFaccioli2008: ['<2,b1,CF,w=0.333333333333>']>

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
0           0           
1           1           
2           2           
=========== ============

Expected data transfer for the sources
--------------------------------------
================================== =======
Number of tasks to generate        1      
Estimated sources to send          1.94 KB
Estimated hazard curves to receive 64 B   
================================== =======