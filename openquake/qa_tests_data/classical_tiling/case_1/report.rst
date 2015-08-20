Classical PSHA using Area Source
================================

Parameters
----------
============================ ================
calculation_mode             classical_tiling
number_of_logic_tree_samples 0               
maximum_distance             200.0           
investigation_time           50.0            
ses_per_logic_tree_path      1               
truncation_level             3.0             
rupture_mesh_spacing         2.0             
complex_fault_mesh_spacing   2.0             
width_of_mfd_bin             0.2             
area_source_discretization   5.0             
random_seed                  23              
master_seed                  0               
concurrent_tasks             32              
============================ ================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================ ===========
smlt_path weight source_model_file                      gsim_logic_tree num_realizations num_sources
========= ====== ====================================== =============== ================ ===========
b1        1.00   `source_model.xml <source_model.xml>`_ simple(2)       2/2              1          
========= ====== ====================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(2)
  0,BooreAtkinson2008: ['<0,b1,b1,w=0.6>']
  0,ChiouYoungs2008: ['<1,b1,b2,w=0.4>']>