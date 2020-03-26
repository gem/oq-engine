Classical PSHA-Based Hazard
===========================

============== ===================
checksum32     2_474_179_155      
date           2020-03-13T11:20:51
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 7, num_levels = 90, num_rlzs = 1

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
area_source_discretization      20.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model_7.xml <exposure_model_7.xml>`_              
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job_haz.ini <job_haz.ini>`_                                
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_fragility    `fragility_model.xml <fragility_model.xml>`_                
======================= ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.21784   482          482         
====== ========= ============ ============

Exposure model
--------------
=========== =
#assets     7
#taxonomies 3
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
Wood     1.00000 0.0    1   1   3         3         
Concrete 1.00000 0.0    1   1   2         2         
Steel    1.00000 0.0    1   1   2         2         
*ALL*    1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      S    482          0.02240   0.21784   482         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.02240  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.02341 NaN    0.02341 0.02341 1      
read_source_model  0.00392 NaN    0.00392 0.00392 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= =========================================== ========
task              sent                                        received
read_source_model                                             1.45 KB 
preclassical      params=1.45 KB srcs=1.38 KB srcfilter=223 B 370 B   
================= =========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66919                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.02341   1.18750   1     
composite source model      0.01363   0.0       1     
total read_source_model     0.00392   0.0       1     
store source_info           0.00217   0.0       1     
reading exposure            4.694E-04 0.0       1     
splitting/filtering sources 3.755E-04 0.0       1     
aggregate curves            3.214E-04 0.0       1     
=========================== ========= ========= ======