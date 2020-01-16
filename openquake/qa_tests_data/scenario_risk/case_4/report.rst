Scenario Risk for Nepal with 20 assets
======================================

============== ===================
checksum32     486_158_159        
date           2020-01-16T05:30:42
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 20, num_levels = 8, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'scenario_risk'   
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 500.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            15.0              
complex_fault_mesh_spacing      15.0              
width_of_mfd_bin                None              
area_source_discretization      None              
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                                
job_ini                  `job.ini <job.ini>`_                                                      
rupture_model            `fault_rupture.xml <fault_rupture.xml>`_                                  
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b_1       1.00000 trivial(1)      1               
========= ======= =============== ================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Exposure model
--------------
=========== ==
#assets     20
#taxonomies 4 
=========== ==

========================== ======= ====== === === ========= ==========
taxonomy                   mean    stddev min max num_sites num_assets
Wood                       1.00000 0.0    1   1   8         8         
Adobe                      1.00000 0.0    1   1   3         3         
Stone-Masonry              1.00000 0.0    1   1   4         4         
Unreinforced-Brick-Masonry 1.00000 0.0    1   1   5         5         
*ALL*                      1.00000 0.0    1   1   20        20        
========================== ======= ====== === === ========= ==========

Information about the tasks
---------------------------
Not available

Data transfer
-------------
==== ==== ========
task sent received
==== ==== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_43210             time_sec  memory_mb counts
====================== ========= ========= ======
ScenarioCalculator.run 0.05639   0.0       1     
saving gmfs            0.00992   0.0       1     
building riskinputs    0.00387   0.0       1     
computing gmfs         0.00144   0.0       1     
reading exposure       7.613E-04 0.0       1     
====================== ========= ========= ======