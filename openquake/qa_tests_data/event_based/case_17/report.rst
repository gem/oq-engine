Event Based Hazard QA Test, Case 17
===================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 5          
maximum_distance             200.0      
investigation_time           1000.0     
ses_per_logic_tree_path      3          
truncation_level             2.0        
rupture_mesh_spacing         1.0        
complex_fault_mesh_spacing   1.0        
width_of_mfd_bin             1.0        
area_source_discretization   10.0       
random_seed                  106        
master_seed                  0          
concurrent_tasks             32         
============================ ===========

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ========================================== =============== ================ ===========
smlt_path weight source_model_file                          gsim_logic_tree num_realizations num_sources
========= ====== ========================================== =============== ================ ===========
b1        0.2    `source_model_1.xml <source_model_1.xml>`_ trivial(0)      1/0              1          
b2        0.2    `source_model_2.xml <source_model_2.xml>`_ trivial(1)      4/1              1          
========= ====== ========================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  1,SadighEtAl1997: ['<1,b2,b1,w=0.2>', '<2,b2,b1,w=0.2>', '<3,b2,b1,w=0.2>', '<4,b2,b1,w=0.2>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
1   b2        active shallow crust 2816        
2   b2        active shallow crust 2775        
3   b2        active shallow crust 2736        
4   b2        active shallow crust 2649        
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
            0           
1           1           
2           2           
3           3           
4           4           
=========== ============

Expected data transfer for the sources
--------------------------------------
================================== =======
Number of tasks to generate        2      
Estimated sources to send          3.97 KB
Estimated hazard curves to receive 24 B   
================================== =======