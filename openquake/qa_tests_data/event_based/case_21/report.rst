Event Based PSHA
================

============== ===================
checksum32     269_549_222        
date           2020-01-16T05:30:59
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    1000              
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      5.0               
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        24                
=============================== ==================

Input files
-----------
======================= ========================
Name                    File                    
======================= ========================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_
job_ini                 `job.ini <job.ini>`_    
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_
======================= ========================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      NaN       2            0.0         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    0.0      
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.02382 NaN    0.02382 0.02382 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ==== ========
task         sent received
SourceReader      28.93 KB
============ ==== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_43265             time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.12292  1.02734   1     
total SourceReader     0.02382  0.0       1     
====================== ======== ========= ======