Scenario Calculation with Simple Fault Rupture
==============================================

num_sites = 7, sitecol = 960 B

Parameters
----------
============================ ========
calculation_mode             scenario
number_of_logic_tree_samples 0       
maximum_distance             200     
investigation_time           None    
ses_per_logic_tree_path      1       
truncation_level             3.0000  
rupture_mesh_spacing         2.0000  
complex_fault_mesh_spacing   2.0000  
width_of_mfd_bin             None    
area_source_discretization   None    
random_seed                  42      
master_seed                  0       
concurrent_tasks             16      
============================ ========

Input files
-----------
============= ========================================
Name          File                                    
============= ========================================
job_ini       `job_haz.ini <job_haz.ini>`_            
rupture_model `rupture_model.xml <rupture_model.xml>`_
sites         `sites.csv <sites.csv>`_                
============= ========================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,BooreAtkinson2008: ['BooreAtkinson2008']>