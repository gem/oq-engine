Scenario Calculation with Simple Fault Rupture
==============================================

============== ===================
checksum32     1,419,232,840      
date           2018-05-15T04:14:26
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 7, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'scenario'        
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
============= ========================================
Name          File                                    
============= ========================================
job_ini       `job_haz.ini <job_haz.ini>`_            
rupture_model `rupture_model.xml <rupture_model.xml>`_
sites         `sites.csv <sites.csv>`_                
============= ========================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b_1       1.00000 trivial(1)      1/1             
========= ======= =============== ================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): [0]>

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
reading site collection 2.372E-04 0.0       1     
======================= ========= ========= ======