Event Based Risk SJ
===================

============== ===================
checksum32     2_863_568_899      
date           2020-03-13T11:21:25
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 61, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== =================
calculation_mode                'preclassical'   
number_of_logic_tree_samples    0                
maximum_distance                {'default': 50.0}
investigation_time              25.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            5.0              
complex_fault_mesh_spacing      5.0              
width_of_mfd_bin                0.3              
area_source_discretization      20.0             
pointsource_distance            {'default': {}}  
ground_motion_correlation_model 'JB2009'         
minimum_intensity               {}               
random_seed                     23               
master_seed                     0                
ses_seed                        42               
=============================== =================

Input files
-----------
======================= ====================================================================
Name                    File                                                                
======================= ====================================================================
gsim_logic_tree         `Costa_Rica_RESIS_II_gmpe_CQ.xml <Costa_Rica_RESIS_II_gmpe_CQ.xml>`_
job_ini                 `job.ini <job.ini>`_                                                
site_model              `site_model_CR_60.xml <site_model_CR_60.xml>`_                      
source_model_logic_tree `sm_lt.xml <sm_lt.xml>`_                                            
======================= ====================================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ===================
grp_id gsims               distances siteparams ruptparams         
====== =================== ========= ========== ===================
0      '[ZhaoEtAl2006Asc]' rrup      vs30       hypo_depth mag rake
====== =================== ========= ========== ===================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3.24167   120          120         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      A    120          0.00448   3.24167   120         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00448  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.01407 NaN    0.01407 0.01407 1      
read_source_model  0.00547 NaN    0.00547 0.00547 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model                                           2.3 KB  
preclassical      srcs=2.19 KB params=620 B srcfilter=223 B 369 B   
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66939                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.01407   0.75391   1     
composite source model      0.01348   0.0       1     
splitting/filtering sources 0.00834   0.0       1     
total read_source_model     0.00547   0.0       1     
store source_info           0.00302   0.0       1     
aggregate curves            2.089E-04 0.0       1     
=========================== ========= ========= ======