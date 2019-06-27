Scenario Risk Maule Mw 8.8 reduced
==================================

============== ===================
checksum32     35,423,337         
date           2019-02-18T08:35:35
engine_version 3.4.0-git9883ae17a5
============== ===================

num_sites = 258, num_levels = 78

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
random_seed                     113            
master_seed                     0              
ses_seed                        42             
avg_losses                      True           
=============================== ===============

Input files
-----------
======================== ==================================================================================
Name                     File                                                                              
======================== ==================================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                                        
gmfs                     `GMFs_Mabe.xml <GMFs_Mabe.xml>`_                                                  
job_ini                  `job.ini <job.ini>`_                                                              
occupants_vulnerability  `occupants_vulnerabilityRes.xml <occupants_vulnerabilityRes.xml>`_                
structural_vulnerability `structural_vulnerability_model_Res.xml <structural_vulnerability_model_Res.xml>`_
======================== ==================================================================================

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
#assets         94      
#taxonomies     35      
deductibile     absolute
insurance_limit absolute
=============== ========

============= ======= ======= === === ========= ==========
taxonomy      mean    stddev  min max num_sites num_assets
LWAL_H1       1.00000 0.0     1   1   3         3         
LWAL_H8       1.00000 NaN     1   1   1         1         
W+WLI_H1      1.00000 0.0     1   1   8         8         
MR_H2_DNO     1.00000 0.0     1   1   4         4         
MR_H1_DNO     1.14286 0.37796 1   2   7         8         
CR+PC_LWAL_H1 1.00000 0.0     1   1   2         2         
LWAL_H1_DNO   1.00000 0.0     1   1   2         2         
MCF_H2        1.00000 0.0     1   1   2         2         
MR_H3_DNO     1.00000 0.0     1   1   3         3         
MCF_H3        1.00000 0.0     1   1   3         3         
LWAL_H2       1.50000 0.70711 1   2   2         3         
LWAL_H2_DNO   1.00000 0.0     1   1   2         2         
LWAL_H7       1.00000 0.0     1   1   2         2         
MCF_H1        1.00000 0.0     1   1   4         4         
MR_H1         1.00000 0.0     1   1   3         3         
MUR+ADO_H1    1.00000 0.0     1   1   2         2         
MUR_H2        1.00000 0.0     1   1   7         7         
LWAL_H5       1.50000 0.70711 1   2   2         3         
MCF_H2_DNO    1.00000 NaN     1   1   1         1         
MR_H2         1.00000 NaN     1   1   1         1         
UNK           1.20000 0.44721 1   2   5         6         
LWAL_H6       1.00000 NaN     1   1   1         1         
W+WS          1.00000 0.0     1   1   3         3         
CR+PC_LWAL_H2 1.00000 NaN     1   1   1         1         
MCF_H3_DNO    1.00000 NaN     1   1   1         1         
MUR_H3        1.00000 0.0     1   1   3         3         
MUR+ST_H1     1.00000 0.0     1   1   2         2         
CR+PC_LWAL_H3 1.00000 NaN     1   1   1         1         
ER+ETR_H2     1.00000 NaN     1   1   1         1         
MUR_H1        1.00000 0.0     1   1   3         3         
ER+ETR_H1     1.00000 NaN     1   1   1         1         
MUR+ADO_H2    1.00000 NaN     1   1   1         1         
W+WLI_H2      1.00000 0.0     1   1   3         3         
MCF_H1_DNO    1.00000 0.0     1   1   2         2         
LWAL_H3       1.00000 NaN     1   1   1         1         
*ALL*         0.36434 1.04705 0   8   258       94        
============= ======= ======= === === ========= ==========

Slowest operations
------------------
=================== ======== ========= ======
operation           time_sec memory_mb counts
=================== ======== ========= ======
building riskinputs 0.04506  0.0       1     
reading exposure    0.00755  0.0       1     
=================== ======== ========= ======