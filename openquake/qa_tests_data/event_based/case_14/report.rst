Hazard South Africa
===================

============== ===================
checksum32     3,741,932,100      
date           2019-06-24T15:33:48
engine_version 3.6.0-git4b6205639c
============== ===================

num_sites = 18, num_levels = 1, num_rlzs = ?

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

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight checksum     
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
9      22        A    89    102   52           0.0       0.0       0.0    2,575,189,190
8      21        A    78    89    168          0.0       0.0       0.0    1,679,964,215
7      20        A    65    78    12,654       0.0       0.0       0.0    4,108,223,530
6      19        A    58    65    6,345        0.0       0.0       0.0    1,573,073,148
5      18        A    51    58    320          0.0       0.0       0.0    3,023,302,063
4      22        A    38    51    8            0.0       0.0       0.0    4,271,785,446
3      21        A    27    38    84           0.0       0.0       0.0    2,620,339,522
2      20        A    14    27    23,199       0.0       0.0       0.0    2,745,271,381
1      19        A    7     14    12,690       0.0       0.0       0.0    1,230,124,462
0      18        A    0     7     480          0.0       0.0       0.0    2,208,689,890
====== ========= ==== ===== ===== ============ ========= ========= ====== =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       10    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.05944 0.06334 0.00570 0.17255 10     
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ================================ ========
task               sent                             received
read_source_models converter=3.06 KB fnames=1.06 KB 26.27 KB
================== ================================ ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.59436  0.0       10    
======================== ======== ========= ======