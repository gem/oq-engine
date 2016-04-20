Scenario Damage
===============

Datastore /home/michele/ssd/calc_11384.hdf5 last updated Wed Apr 20 09:36:46 2016 on gem-tstation

num_sites = 7, sitecol = 690 B

Parameters
----------
============================ ===================
calculation_mode             'scenario_damage'  
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           None               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             None               
area_source_discretization   None               
random_seed                  42                 
master_seed                  0                  
oqlite_version               '0.13.0-git361357f'
============================ ===================

Input files
-----------
==================== ============================================
Name                 File                                        
==================== ============================================
exposure             `exposure_model.xml <exposure_model.xml>`_  
job_ini              `job.ini <job.ini>`_                        
rupture_model        `rupture_model.xml <rupture_model.xml>`_    
sites                `sites.csv <sites.csv>`_                    
structural_fragility `fragility_model.xml <fragility_model.xml>`_
==================== ============================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,BooreAtkinson2008: ['BooreAtkinson2008']>

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== =======
Taxonomy #Assets
======== =======
Wood     1      
======== =======

Slowest operations
------------------
========================= ========= ========= ======
operation                 time_sec  memory_mb counts
========================= ========= ========= ======
computing individual risk 0.021     0.0       1     
filtering sites           0.008     0.0       1     
reading exposure          0.002     0.0       1     
computing gmfs            6.821E-04 0.0       1     
saving gmfs               5.798E-04 0.0       1     
assoc_assets_sites        4.861E-04 0.0       1     
reading site collection   1.180E-04 0.0       1     
building riskinputs       7.701E-05 0.0       1     
getting hazard            1.311E-05 0.0       1     
========================= ========= ========= ======