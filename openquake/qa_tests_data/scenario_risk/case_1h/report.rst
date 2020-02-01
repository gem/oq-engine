scenario risk
=============

============== ===================
checksum32     1_429_593_239      
date           2020-01-16T05:30:43
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 2, num_levels = 8, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'scenario_risk'   
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
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
======================== ====================================================
Name                     File                                                
======================== ====================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_          
job_ini                  `job.ini <job.ini>`_                                
rupture_model            `rupture_model.xml <rupture_model.xml>`_            
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_
======================== ====================================================

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
#assets     2
#taxonomies 1
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   2         2         
======== ======= ====== === === ========= ==========

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
calc_43221             time_sec  memory_mb counts
====================== ========= ========= ======
ScenarioCalculator.run 0.04180   0.0       1     
saving gmfs            0.00375   0.0       1     
building riskinputs    9.916E-04 0.0       1     
reading exposure       5.481E-04 0.0       1     
computing gmfs         4.458E-04 0.0       1     
====================== ========= ========= ======