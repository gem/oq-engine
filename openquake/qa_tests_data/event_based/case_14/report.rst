Hazard South Africa
===================

============== ===================
checksum32     2_508_160_232      
date           2020-01-16T05:31:00
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 10, num_levels = 1, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    3                 
maximum_distance                {'default': 100.0}
investigation_time              100.0             
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     113               
master_seed                     0                 
ses_seed                        23                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_                                    
job_ini                 `job.ini <job.ini>`_                                        
site_model              `Site_model_South_Africa.xml <Site_model_South_Africa.xml>`_
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_                                    
======================= ============================================================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      NaN       480          0.0         
1      NaN       12_690       0.0         
2      NaN       23_199       0.0         
3      NaN       84           0.0         
4      NaN       8            0.0         
5      NaN       320          0.0         
6      NaN       6_345        0.0         
7      NaN       12_654       0.0         
8      NaN       168          0.0         
9      NaN       52           0.0         
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
A    0.0      
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.10793 0.12022 0.00956 0.32824 10     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ================================================ ========
task         sent                                             received
SourceReader apply_unc=40.83 KB ltmodel=3.29 KB fname=1.04 KB 34.36 KB
============ ================================================ ========

Slowest operations
------------------
====================== ======== ========= ======
calc_43272             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     1.07928  0.07812   10    
composite source model 0.35848  1.02734   1     
====================== ======== ========= ======