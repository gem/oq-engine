Scenario Damage
===============

gem-tstation:/home/michele/ssd/calc_15395.hdf5 updated Tue May 10 12:35:38 2016

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
oqlite_version               '0.13.0-gitcdd89a9'
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
  0,BooreAtkinson2008(): ['BooreAtkinson2008()']>

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
Wood     1.000 NaN    1   1   1         1         
======== ===== ====== === === ========= ==========

Information about the tasks
---------------------------
========================= ===== ====== ===== ===== =========
measurement               mean  stddev min   max   num_tasks
scenario_damage.time_sec  0.046 NaN    0.046 0.046 1        
scenario_damage.memory_mb 0.004 NaN    0.004 0.004 1        
========================= ===== ====== ===== ===== =========

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
total scenario_damage   0.046     0.004     1     
computing riskmodel     0.045     0.0       1     
filtering sites         0.009     0.0       1     
reading exposure        0.003     0.0       1     
saving gmfs             0.001     0.0       1     
computing gmfs          0.001     0.0       1     
assoc_assets_sites      5.920E-04 0.0       1     
reading site collection 1.099E-04 0.0       1     
building riskinputs     8.917E-05 0.0       1     
building hazard         3.695E-05 0.0       1     
======================= ========= ========= ======