British Columbia With Vs30
==========================

============== ===================
checksum32     226,163,923        
date           2019-09-24T15:21:05
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 2, num_levels = 3, num_rlzs = ?

Parameters
----------
=============================== ========================================================================
calculation_mode                'event_based'                                                           
number_of_logic_tree_samples    0                                                                       
maximum_distance                {'default': 800.0, 'Active Shallow Offshore': 800.0}                    
investigation_time              20.0                                                                    
ses_per_logic_tree_path         1                                                                       
truncation_level                3.0                                                                     
rupture_mesh_spacing            5.0                                                                     
complex_fault_mesh_spacing      10.0                                                                    
width_of_mfd_bin                0.1                                                                     
area_source_discretization      15.0                                                                    
ground_motion_correlation_model None                                                                    
minimum_intensity               {'SA(0.3)': 0.001, 'SA(0.6)': 0.001, 'SA(1.0)': 0.001, 'default': 0.001}
random_seed                     24                                                                      
master_seed                     0                                                                       
ses_seed                        23                                                                      
=============================== ========================================================================

Input files
-----------
======================= =====================================================
Name                    File                                                 
======================= =====================================================
exposure                `BC_Exposure.xml <BC_Exposure.xml>`_                 
gsim_logic_tree         `gmmLT_analytical.xml <gmmLT_analytical.xml>`_       
job_ini                 `job.ini <job.ini>`_                                 
site_model              `vs30_a.xml <vs30_a.xml>`_ `vs30_b.xml <vs30_b.xml>`_
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_                             
======================= =====================================================

Exposure model
--------------
=========== =
#assets     2
#taxonomies 2
=========== =

========== ======= ======= === === ========= ==========
taxonomy   mean    stddev  min max num_sites num_assets
RES1-W1-HC 1.00000 NaN     1   1   1         1         
RES1-W1-LC 1.00000 NaN     1   1   1         1         
*ALL*      0.22222 0.44096 0   1   9         2         
========== ======= ======= === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       5     
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 2 duplicate sources with multiplicity 2.5: ['OFS' 'OFS']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.05476 0.01166 0.04512 0.07208 5      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================== ========
task               sent                           received
read_source_models converter=1.74 KB fnames=585 B 13.98 KB
================== ============================== ========

Slowest operations
------------------
======================== ======== ========= ======
calc_1784                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.27380  0.0       5     
reading exposure         0.00154  0.0       1     
======================== ======== ========= ======