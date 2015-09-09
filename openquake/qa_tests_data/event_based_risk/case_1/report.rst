PEB QA test 1
=============

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             100.0      
investigation_time           50.0       
ses_per_logic_tree_path      2000       
truncation_level             3.0        
rupture_mesh_spacing         5.0        
complex_fault_mesh_spacing   5.0        
width_of_mfd_bin             0.3        
area_source_discretization   10.0       
random_seed                  23         
master_seed                  0          
concurrent_tasks             32         
============================ ===========

Input files
-----------
=========================== ====================================================================
Name                        File                                                                
=========================== ====================================================================
contents_vulnerability      `vulnerability_model_coco.xml <vulnerability_model_coco.xml>`_      
gsim_logic_tree             `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                        
job_ini                     `job_haz.ini <job_haz.ini>`_                                        
nonstructural_vulnerability `vulnerability_model_nonstco.xml <vulnerability_model_nonstco.xml>`_
source                      `source_model.xml <source_model.xml>`_                              
source_model_logic_tree     `source_model_logic_tree.xml <source_model_logic_tree.xml>`_        
structural_vulnerability    `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_      
=========================== ====================================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================ ===========
smlt_path weight source_model_file                      gsim_logic_tree num_realizations num_sources
========= ====== ====================================== =============== ================ ===========
b1        1.00   `source_model.xml <source_model.xml>`_ simple(2)       2/2              3          
========= ====== ====================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(2)
  0,AkkarBommer2010: ['<1,b1,b2,w=0.5>']
  0,ChiouYoungs2008: ['<0,b1,b1,w=0.5>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b1        Active Shallow Crust 2284        
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
0           0 1         
=========== ============

Expected data transfer for the sources
--------------------------------------
================================== =======
Number of tasks to generate        1      
Estimated sources to send          2.73 KB
Estimated hazard curves to receive 1 KB   
================================== =======