Scenario QA Test with Spatial Correlation - Case 2
==================================================

Datastore /home/michele/ssd/calc_11392.hdf5 last updated Wed Apr 20 09:36:47 2016 on gem-tstation

num_sites = 2, sitecol = 785 B

Parameters
----------
============================ ===================
calculation_mode             'scenario'         
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200}   
investigation_time           None               
ses_per_logic_tree_path      1                  
truncation_level             None               
rupture_mesh_spacing         1.0                
complex_fault_mesh_spacing   1.0                
width_of_mfd_bin             None               
area_source_discretization   None               
random_seed                  3                  
master_seed                  0                  
oqlite_version               '0.13.0-git361357f'
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
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
filtering sites         0.009     0.0       1     
computing gmfs          0.004     0.0       1     
reading site collection 2.789E-05 0.0       1     
======================= ========= ========= ======