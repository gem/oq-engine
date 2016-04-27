Scenario QA Test for occupants
==============================

gem-tstation:/home/michele/ssd/calc_118.hdf5 updated Wed Apr 27 10:57:13 2016

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ===================
calculation_mode             'scenario'         
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 300}   
investigation_time           None               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         10.0               
complex_fault_mesh_spacing   10.0               
width_of_mfd_bin             None               
area_source_discretization   None               
random_seed                  3                  
master_seed                  0                  
oqlite_version               '0.13.0-gitcbbc4a8'
============================ ===================

Input files
-----------
======================= ========================================================================
Name                    File                                                                    
======================= ========================================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                              
job_ini                 `job_haz.ini <job_haz.ini>`_                                            
occupants_vulnerability `vulnerability_model_occupants.xml <vulnerability_model_occupants.xml>`_
rupture_model           `fault_rupture.xml <fault_rupture.xml>`_                                
======================= ========================================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,ChiouYoungs2008: ['ChiouYoungs2008']>

Exposure model
--------------
=========== =
#assets     3
#taxonomies 3
=========== =

======== =======
Taxonomy #Assets
======== =======
RC       1      
RM       1      
W        1      
======== =======

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
filtering sites         0.007     0.0       1     
reading exposure        0.003     0.0       1     
computing gmfs          0.001     0.0       1     
reading site collection 8.106E-06 0.0       1     
======================= ========= ========= ======