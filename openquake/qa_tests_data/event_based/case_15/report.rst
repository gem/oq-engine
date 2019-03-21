Hazard Japan (HERP model 2014) reduced
======================================

============== ===================
checksum32     2,896,463,652      
date           2019-03-19T10:04:09
engine_version 3.5.0-gitad6b69ea66
============== ===================

num_sites = 5, num_levels = 1, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     113               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ==============================================
Name                    File                                          
======================= ==============================================
gsim_logic_tree         `gmmLT_sa.xml <gmmLT_sa.xml>`_                
job_ini                 `job.ini <job.ini>`_                          
site_model              `Site_model_Japan.xml <Site_model_Japan.xml>`_
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_                      
======================= ==============================================

Slowest sources
---------------
====== ================== ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id          code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ================== ==== ===== ===== ============ ========= ========== ========= ========= ======
1      case_02            N    1     159   1            0.0       0.0        0.0       1         0.0   
0      gs_PSE_CPCF_2_1228 P    0     1     26           0.0       0.0        0.0       1         0.0   
====== ================== ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.0       1     
P    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.00223 NaN       0.00223 0.00223 1      
only_filter        0.00252 8.514E-05 0.00246 0.00258 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ======================================= ========
task               sent                                    received
read_source_models converter=313 B fnames=119 B            6.62 KB 
only_filter        srcs=6.67 KB srcfilter=506 B dummy=28 B 6.47 KB 
================== ======================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total only_filter        0.00503  1.55078   2     
total read_source_models 0.00223  0.00391   1     
======================== ======== ========= ======