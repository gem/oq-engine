Event-based PSHA producing hazard curves only
=============================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             200.0      
investigation_time           50.0       
ses_per_logic_tree_path      300        
truncation_level             3.0        
rupture_mesh_spacing         2.0        
complex_fault_mesh_spacing   2.0        
width_of_mfd_bin             0.2        
area_source_discretization   20.0       
random_seed                  23         
master_seed                  0          
concurrent_tasks             32         
============================ ===========

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model1.xml <source_model1.xml>`_                    
source                  `source_model2.xml <source_model2.xml>`_                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ======================================== =============== ================ ===========
smlt_path weight source_model_file                        gsim_logic_tree num_realizations num_sources
========= ====== ======================================== =============== ================ ===========
b11       0.60   `source_model1.xml <source_model1.xml>`_ simple(3)       3/3              307        
b12       0.40   `source_model2.xml <source_model2.xml>`_ simple(3)       3/3              307        
========= ====== ======================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(6)
  0,BooreAtkinson2008: ['<0,b11,b11,w=0.3>']
  0,CampbellBozorgnia2008: ['<1,b11,b12,w=0.18>']
  0,ChiouYoungs2008: ['<2,b11,b13,w=0.12>']
  1,BooreAtkinson2008: ['<3,b12,b11,w=0.2>']
  1,CampbellBozorgnia2008: ['<4,b12,b12,w=0.12>']
  1,ChiouYoungs2008: ['<5,b12,b13,w=0.08>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b11       Active Shallow Crust 14413       
1   b12       Active Shallow Crust 1429        
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
0           0 1 2       
1           3 4 5       
=========== ============

Expected data transfer for the sources
--------------------------------------
================================== =========
Number of tasks to generate        34       
Estimated sources to send          189.21 KB
Estimated hazard curves to receive 3 KB     
================================== =========