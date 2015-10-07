Scenario Calculation with Simple Fault Rupture
==============================================

Parameters
----------
============================ ========
calculation_mode             scenario
number_of_logic_tree_samples 0       
maximum_distance             200.0   
investigation_time           None    
ses_per_logic_tree_path      1       
truncation_level             3.0     
rupture_mesh_spacing         2.0     
complex_fault_mesh_spacing   2.0     
width_of_mfd_bin             None    
area_source_discretization   None    
random_seed                  42      
master_seed                  0       
concurrent_tasks             64      
============================ ========

Input files
-----------
=============== ============================================
Name            File                                        
=============== ============================================
gsim_logic_tree `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_
job_ini         `job_haz.ini <job_haz.ini>`_                
rupture_model   `rupture_model.xml <rupture_model.xml>`_    
=============== ============================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(2)
  0,BooreAtkinson2008: ['BooreAtkinson2008']
  0,ChiouYoungs2008: ['ChiouYoungs2008']>