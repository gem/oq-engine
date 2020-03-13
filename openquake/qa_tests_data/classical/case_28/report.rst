North Africa PSHA
=================

============== ===================
checksum32     2_135_452_217      
date           2020-03-13T11:23:06
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 2, num_levels = 133, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     19                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
sites                   `sites.csv <sites.csv>`_                                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============================= ======= ================
smlt_path                     weight  num_realizations
============================= ======= ================
smoothed_model_m_m0.2_b_e0.0  0.50000 1               
smoothed_model_m_m0.2_b_m0.05 0.50000 1               
============================= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== =========== ========= ========== ==========
grp_id gsims       distances siteparams ruptparams
====== =========== ========= ========== ==========
0      '[AvgGMPE]'                                
1      '[AvgGMPE]'                                
====== =========== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.00435   460          460         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
21        0      M    460          0.00304   0.00435   460         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
M    0.00304  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00485 NaN    0.00485 0.00485 1      
read_source_model  0.00119 NaN    0.00119 0.00119 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ======================================= ========
task              sent                                    received
read_source_model                                         1.84 KB 
preclassical      params=2.06 KB srcs=1.76 KB gsims=632 B 370 B   
================= ======================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_67007                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.01299   0.0       1     
total preclassical          0.00485   0.0       1     
store source_info           0.00205   0.0       1     
total read_source_model     0.00119   0.0       1     
splitting/filtering sources 0.00100   0.0       1     
aggregate curves            2.110E-04 0.0       1     
=========================== ========= ========= ======