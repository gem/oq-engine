Germany_SHARE Combined Model event_based
========================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             80.0       
investigation_time           30.0       
ses_per_logic_tree_path      1          
truncation_level             3.0        
rupture_mesh_spacing         5.0        
complex_fault_mesh_spacing   5.0        
width_of_mfd_bin             0.1        
area_source_discretization   10.0       
random_seed                  23         
master_seed                  0          
concurrent_tasks             32         
============================ ===========

Input files
-----------
======================= ==============================================================================
Name                    File                                                                          
======================= ==============================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                                          
sites                   `sites.csv <sites.csv>`_                                                      
source                  `as_model.xml <as_model.xml>`_                                                
source                  `fs_bg_source_model.xml <fs_bg_source_model.xml>`_                            
source                  `ss_model_final_250km_Buffer.xml <ss_model_final_250km_Buffer.xml>`_          
source_model_logic_tree `combined_logic-tree-source-model.xml <combined_logic-tree-source-model.xml>`_
======================= ==============================================================================

Composite source model
----------------------
========= ====== ================================================================================================ ================ ================ ===========
smlt_path weight source_model_file                                                                                gsim_logic_tree  num_realizations num_sources
========= ====== ================================================================================================ ================ ================ ===========
b1        0.50   `source_models/as_model.xml <source_models/as_model.xml>`_                                       trivial(0,0,0,0) 0/0              12         
b2        0.200  `source_models/fs_bg_source_model.xml <source_models/fs_bg_source_model.xml>`_                   simple(0,0,5,0)  5/5              25331      
b3        0.300  `source_models/ss_model_final_250km_Buffer.xml <source_models/ss_model_final_250km_Buffer.xml>`_ trivial(0,0,0,0) 0/0              36         
========= ====== ================================================================================================ ================ ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(5)
  4,AkkarBommer2010: ['<0,b2,@_b2_1_@_@,w=0.2>']
  4,Campbell2003SHARE: ['<4,b2,@_b2_5_@_@,w=0.2>']
  4,CauzziFaccioli2008: ['<1,b2,@_b2_2_@_@,w=0.2>']
  4,ChiouYoungs2008: ['<2,b2,@_b2_3_@_@,w=0.2>']
  4,ToroEtAl2002SHARE: ['<3,b2,@_b2_4_@_@,w=0.2>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
4   b2        Stable Shallow Crust 2           
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
4           0 1 2 3 4   
=========== ============

Expected data transfer for the sources
--------------------------------------
================================== =======
Number of tasks to generate        35     
Estimated sources to send          6.29 MB
Estimated hazard curves to receive 0 B    
================================== =======