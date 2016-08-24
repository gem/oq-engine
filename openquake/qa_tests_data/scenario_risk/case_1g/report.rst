Scenario Calculation with Simple Fault Rupture
==============================================

gem-tstation:/home/michele/ssd/calc_42037.hdf5 updated Wed Aug 24 08:05:16 2016

num_sites = 7, sitecol = 1015 B

Parameters
----------
============================ ===================
calculation_mode             'scenario'         
number_of_logic_tree_samples 0                  
maximum_distance             {u'default': 200.0}
investigation_time           None               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             None               
area_source_discretization   None               
random_seed                  42                 
master_seed                  0                  
engine_version               '2.1.0-git46eb8e0' 
============================ ===================

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

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): ['<0,b_1~b1,w=1.0>']>

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
filtering sites         0.006     0.0       1     
reading site collection 7.892E-05 0.0       1     
======================= ========= ========= ======