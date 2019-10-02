Scenario Risk with site model
=============================

============== ===================
checksum32     3,193,187,389      
date           2019-10-02T10:07:11
engine_version 3.8.0-git6f03622c6e
============== ===================

num_sites = 8, num_levels = 106, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'scenario_risk'   
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
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure_roads_bridges.xml <exposure_roads_bridges.xml>`_                
job_ini                  `job.ini <job.ini>`_                                                      
rupture_model            `fault_rupture.xml <fault_rupture.xml>`_                                  
site_model               `VS30_grid_0.05_towns.xml <VS30_grid_0.05_towns.xml>`_                    
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
=========== =
#assets     9
#taxonomies 4
=========== =

============ ======= ======= === === ========= ==========
taxonomy     mean    stddev  min max num_sites num_assets
EMCA_PRIM_2L 1.00000 0.0     1   1   3         3         
EMCA_PRIM_4L 1.00000 NaN     1   1   1         1         
concrete_spl 1.00000 0.0     1   1   2         2         
steel_spl    1.00000 0.0     1   1   3         3         
*ALL*        0.03704 0.20995 0   2   243       9         
============ ======= ======= === === ========= ==========

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
====================== ======== ========= ======
calc_29417             time_sec memory_mb counts
====================== ======== ========= ======
ScenarioCalculator.run 0.15104  0.60547   1     
building riskinputs    0.01273  0.0       1     
saving gmfs            0.00505  0.34375   1     
computing gmfs         0.00404  0.06641   1     
reading exposure       0.00288  0.0       1     
====================== ======== ========= ======