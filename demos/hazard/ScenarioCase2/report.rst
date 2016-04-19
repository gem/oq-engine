Scenario Calculation with Complex Fault Rupture
===============================================

Datastore /home/michele/ssd/calc_10530.hdf5 last updated Tue Apr 19 05:57:12 2016 on gem-tstation

num_sites = 352, sitecol = 16.52 KB

Parameters
----------
============================ ===================
calculation_mode             'scenario'         
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200}   
investigation_time           None               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             None               
area_source_discretization   None               
random_seed                  3                  
master_seed                  0                  
oqlite_version               '0.13.0-git7c9cf8e'
============================ ===================

Input files
-----------
============= ========================================
Name          File                                    
============= ========================================
job_ini       `job.ini <job.ini>`_                    
rupture_model `rupture_model.xml <rupture_model.xml>`_
============= ========================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,BooreAtkinson2008: ['BooreAtkinson2008']>

Slowest operations
------------------
======================= ======== ========= ======
operation               time_sec memory_mb counts
======================= ======== ========= ======
filtering sites         0.077    0.0       1     
reading site collection 0.047    0.0       1     
computing gmfs          0.040    0.0       1     
======================= ======== ========= ======