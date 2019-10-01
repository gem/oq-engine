Ucerf test
==========

============== ===================
checksum32     87,673,300         
date           2019-10-01T07:00:53
engine_version 3.8.0-gitbd71c2f960
============== ===================

num_sites = 155, num_levels = 6, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'ucerf_hazard'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              200.0             
ses_per_logic_tree_path         3                 
truncation_level                None              
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {'default': 0.1}  
random_seed                     1066              
master_seed                     0                 
ses_seed                        1066              
=============================== ==================

Input files
-----------
======================= ====================================================================
Name                    File                                                                
======================= ====================================================================
gsim_logic_tree         `gmpe_logic_tree_ucerf_mean.xml <gmpe_logic_tree_ucerf_mean.xml>`_  
job_ini                 `job.ini <job.ini>`_                                                
sites                   `bay_area.csv <bay_area.csv>`_                                      
source_model            `dummy_ucerf_bg_source_redux.xml <dummy_ucerf_bg_source_redux.xml>`_
source_model_logic_tree `dummy_ucerf_smlt_redux.xml <dummy_ucerf_smlt_redux.xml>`_          
======================= ====================================================================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      -1.0      0            1000        
1      -1.0      0            1000        
2      -1.0      0            1000        
3      -1.0      0            1000        
4      -1.0      0            1000        
5      -1.0      0            1000        
6      -1.0      0            1000        
7      -1.0      0            1000        
8      -1.0      0            1000        
9      -1.0      0            1000        
10     -1.0      0            1000        
11     -1.0      0            1000        
12     -1.0      0            1000        
13     -1.0      0            1000        
14     -1.0      0            1000        
15     -1.0      0            1000        
16     -1.0      0            1000        
17     -1.0      0            1000        
18     -1.0      0            1000        
19     -1.0      0            1000        
20     -1.0      0            1000        
21     -1.0      0            1000        
22     -1.0      0            1000        
23     -1.0      0            1000        
====== ========= ============ ============

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
U    0.0       24    
==== ========= ======

Information about the tasks
---------------------------
Not available

Data transfer
-------------
==== ==== ========
task sent received
==== ==== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_6559              time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.02783  0.0       1     
====================== ======== ========= ======