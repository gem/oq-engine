Escenario Santiago DC - Daño y pérdidas
=======================================

============== ===================
checksum32     636,647,998        
date           2019-10-23T16:26:02
engine_version 3.8.0-git2e0d8e6795
============== ===================

num_sites = 10, num_levels = 202, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'scenario_damage' 
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     113               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
====================== ======================================================================
Name                   File                                                                  
====================== ======================================================================
exposure               `exposure_model.xml <exposure_model.xml>`_                            
gsim_logic_tree        `gmpe.xml <gmpe.xml>`_                                                
job_ini                `job.ini <job.ini>`_                                                  
rupture_model          `earthquake_rupture_model.xml <earthquake_rupture_model.xml>`_        
structural_consequence `ccara_consequence_model_CARA.xml <ccara_consequence_model_CARA.xml>`_
structural_fragility   `ccara_fragility_model_CARA.xml <ccara_fragility_model_CARA.xml>`_    
====================== ======================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b_1       1.00000 simple(2)       2               
========= ======= =============== ================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=2)>

Exposure model
--------------
=========== ==
#assets     10
#taxonomies 8 
=========== ==

=============== ======= ====== === === ========= ==========
taxonomy        mean    stddev min max num_sites num_assets
MR_LWAL-DNO_H2  1.00000 NaN    1   1   1         1         
MR_LWAL-DNO_H3  1.00000 0.0    1   1   2         2         
MUR_LWAL-DNO_H1 1.00000 NaN    1   1   1         1         
MCF_LWAL-DNO_H3 1.00000 0.0    1   1   2         2         
CR_LFINF-DUH_H4 1.00000 NaN    1   1   1         1         
W-WS_LPB-DNO_H1 1.00000 NaN    1   1   1         1         
MR_LWAL-DNO_H1  1.00000 NaN    1   1   1         1         
CR_LFINF-DUH_H2 1.00000 NaN    1   1   1         1         
*ALL*           1.00000 0.0    1   1   10        10        
=============== ======= ====== === === ========= ==========

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
calc_44452             time_sec memory_mb counts
====================== ======== ========= ======
ScenarioCalculator.run 0.17265  1.71484   1     
saving gmfs            0.07408  1.71484   1     
building riskinputs    0.03959  0.0       1     
computing gmfs         0.01008  0.0       1     
reading exposure       0.00225  0.0       1     
====================== ======== ========= ======