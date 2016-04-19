Scenario Damage
===============

Datastore /home/michele/ssd/calc_10486.hdf5 last updated Tue Apr 19 05:56:35 2016 on gem-tstation

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
oqlite_version               '0.13.0-git7c9cf8e'
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
computing individual risk 0.027     0.0       1     
filtering sites           0.009     0.0       1     
reading exposure          0.003     0.0       1     
computing gmfs            8.631E-04 0.0       1     
saving gmfs               7.401E-04 0.0       1     
assoc_assets_sites        5.832E-04 0.0       1     
reading site collection   1.101E-04 0.0       1     
building riskinputs       1.061E-04 0.0       1     
getting hazard            1.717E-05 0.0       1     
========================= ========= ========= ======