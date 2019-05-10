Kish pga
========

============== ===================
checksum32     4,282,897,091      
date           2019-05-10T05:07:14
engine_version 3.5.0-gitbaeb4c1e35
============== ===================

num_sites = 63, num_levels = 13, num_rlzs = 1

Parameters
----------
=============================== ===============
calculation_mode                'scenario_risk'
number_of_logic_tree_samples    0              
maximum_distance                None           
investigation_time              None           
ses_per_logic_tree_path         1              
truncation_level                None           
rupture_mesh_spacing            None           
complex_fault_mesh_spacing      None           
width_of_mfd_bin                None           
area_source_discretization      None           
ground_motion_correlation_model None           
minimum_intensity               {}             
random_seed                     42             
master_seed                     0              
ses_seed                        42             
avg_losses                      True           
=============================== ===============

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exp_part2.xml <exp_part2.xml>`_                                          
gmfs                     `gmf475.xml <gmf475.xml>`_                                                
job_ini                  `job.ini <job.ini>`_                                                      
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

  <RlzsAssoc(size=1, rlzs=1)
  0,'[FromFile]': [0]>

Number of ruptures per tectonic region type
-------------------------------------------
============ ====== === ============ ============
source_model grp_id trt eff_ruptures tot_ruptures
============ ====== === ============ ============
scenario     0      *   1            0           
============ ====== === ============ ============

Exposure model
--------------
=============== ========
#assets         5       
#taxonomies     2       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ======= === === ========= ==========
taxonomy mean    stddev  min max num_sites num_assets
RC1      4.00000 NaN     4   4   1         4         
ST1      1.00000 NaN     1   1   1         1         
*ALL*    0.07937 0.51749 0   4   63        5         
======== ======= ======= === === ========= ==========

Slowest operations
------------------
=================== ======== ========= ======
operation           time_sec memory_mb counts
=================== ======== ========= ======
building riskinputs 0.00283  0.0       1     
reading exposure    0.00101  0.0       1     
=================== ======== ========= ======