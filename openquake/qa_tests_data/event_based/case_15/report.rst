Hazard Japan (HERP model 2014) reduced
======================================

============== ===================
checksum32     3,185,838,388      
date           2018-10-05T03:04:50
engine_version 3.3.0-git48e9a474fd
============== ===================

num_sites = 5, num_levels = 1

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
=============== ==============================================
Name            File                                          
=============== ==============================================
gsim_logic_tree `gmmLT_sa.xml <gmmLT_sa.xml>`_                
job_ini         `job.ini <job.ini>`_                          
site_model      `Site_model_Japan.xml <Site_model_Japan.xml>`_
source          `ssm01.xml <ssm01.xml>`_                      
source_model    `ssm01.xml <ssm01.xml>`_                      
=============== ==============================================

Slowest sources
---------------
====== ================== ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id          code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ================== ==== ===== ===== ============ ========= ========== ========= ========= ======
0      gs_PSE_CPCF_2_1228 P    0     1     26           0.0       1.645E-05  0.0       1         0.0   
1      case_02            N    1     159   1            0.0       1.311E-05  0.0       1         0.0   
====== ================== ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.0       1     
P    0.0       1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.00200 NaN    0.00200 0.00200 1      
split_filter       0.00337 NaN    0.00337 0.00337 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ======================================================================= ========
task               sent                                                                    received
read_source_models monitor=0 B fnames=0 B converter=0 B                                    6.52 KB 
split_filter       srcs=6.23 KB monitor=425 B srcfilter=220 B sample_factor=21 B seed=14 B 6.31 KB 
================== ======================================================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
updating source_info     0.00902  0.0       1     
total split_filter       0.00337  0.0       1     
total read_source_models 0.00200  0.0       1     
======================== ======== ========= ======