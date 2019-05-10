British Columbia With Vs30
==========================

============== ===================
checksum32     2,623,339,741      
date           2019-05-10T05:07:29
engine_version 3.5.0-gitbaeb4c1e35
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
=============== ========
#assets         2       
#taxonomies     2       
deductibile     absolute
insurance_limit absolute
=============== ========

========== ======= ====== === === ========= ==========
taxonomy   mean    stddev min max num_sites num_assets
RES1-W1-HC 1.00000 NaN    1   1   1         1         
RES1-W1-LC 1.00000 NaN    1   1   1         1         
*ALL*      1.00000 0.0    1   1   2         2         
========== ======= ====== === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
4      OFS       A    29    37    15,618       0.0       0.0       0.0   
3      OFS       A    22    29    8,778        0.0       0.0       0.0   
2      OFS       A    15    22    8,778        0.0       0.0       0.0   
1      OFS       A    7     15    15,618       0.0       0.0       0.0   
0      OFS       A    0     7     8,778        0.0       0.0       0.0   
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       5     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.05397 0.01286 0.04271 0.07197 5      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================== ========
task               sent                           received
read_source_models converter=1.74 KB fnames=585 B 13.96 KB
================== ============================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.26985  0.0       5     
reading exposure         0.00145  0.0       1     
======================== ======== ========= ======