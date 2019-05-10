Reduced Hazard Italy
====================

============== ===================
checksum32     1,879,307,037      
date           2019-05-10T05:07:28
engine_version 3.5.0-gitbaeb4c1e35
============== ===================

num_sites = 148, num_levels = 30, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              200.0             
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     113               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure.xml <exposure.xml>`_                              
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
site_model              `site_model.csv <site_model.csv>`_                          
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Exposure model
--------------
=============== ========
#assets         151     
#taxonomies     17      
deductibile     absolute
insurance_limit absolute
=============== ========

================= ======= ======= === === ========= ==========
taxonomy          mean    stddev  min max num_sites num_assets
CR/CDN/HBET:1-2   1.00000 0.0     1   1   8         8         
CR/CDM/HBET:1-2   1.00000 0.0     1   1   13        13        
CR/CDM/HBET:3-5   1.00000 0.0     1   1   14        14        
CR/CDN/H:4        1.00000 0.0     1   1   2         2         
MUR/LWAL/HBET:5-8 1.00000 0.0     1   1   6         6         
CR/CDM/HBET:6-8   1.00000 0.0     1   1   3         3         
MUR/LWAL/H:3      1.00000 0.0     1   1   18        18        
CR/CDM/SOS        1.00000 0.0     1   1   10        10        
MUR/LWAL/HBET:1-2 1.00000 0.0     1   1   17        17        
CR/CDN/SOS        1.00000 0.0     1   1   10        10        
W/CDN/HBET:1-3    1.00000 0.0     1   1   14        14        
CR/CDH/HBET:1-2   1.00000 0.0     1   1   11        11        
CR/CDH/HBET:6-8   1.00000 0.0     1   1   3         3         
MUR/LWAL/H:4      1.00000 0.0     1   1   8         8         
CR/CDH/HBET:3-5   1.00000 0.0     1   1   9         9         
S/CDM/HBET:4-8    1.00000 0.0     1   1   2         2         
CR/CDN/H:3        1.00000 0.0     1   1   3         3         
*ALL*             1.02027 0.14140 1   2   148       151       
================= ======= ======= === === ========= ==========

Slowest sources
---------------
====== ========== ==== ===== ===== ============ ========= ========= ======
grp_id source_id  code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========== ==== ===== ===== ============ ========= ========= ======
0      AS_HRAS083 A    0     15    2,295        0.0       0.0       0.0   
====== ========== ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.02785 NaN    0.02785 0.02785 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ============================ ========
task               sent                         received
read_source_models converter=313 B fnames=110 B 2.86 KB 
================== ============================ ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.02785  0.0       1     
reading exposure         0.00245  0.0       1     
======================== ======== ========= ======