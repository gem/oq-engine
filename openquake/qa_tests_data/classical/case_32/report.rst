Classical PSHA with site class as a site variable
=================================================

============== ===================
checksum32     1_357_757_930      
date           2020-03-13T11:22:59
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 14, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.1               
area_source_discretization      None              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
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
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
smb1      1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================== ========= ========== ===================
grp_id gsims                distances siteparams ruptparams         
====== ==================== ========= ========== ===================
0      '[McVerry2006AscSC]' rrup      siteclass  hypo_depth mag rake
====== ==================== ========= ========== ===================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.03226   310          310         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
2         0      S    310          0.01444   0.03226   310         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.01444  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.01542 NaN    0.01542 0.01542 1      
read_source_model  0.00564 NaN    0.00564 0.00564 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model                                           1.52 KB 
preclassical      srcs=1.39 KB params=728 B srcfilter=223 B 370 B   
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_67004                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.01558   0.0       1     
total preclassical          0.01542   1.22656   1     
total read_source_model     0.00564   0.0       1     
store source_info           0.00246   0.0       1     
aggregate curves            4.177E-04 0.0       1     
splitting/filtering sources 3.808E-04 0.0       1     
=========================== ========= ========= ======