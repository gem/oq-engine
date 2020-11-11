Event Based Risk SJ
===================

============== ====================
checksum32     1_678_874_745       
date           2020-11-02T09:36:09 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 61, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ========================================
calculation_mode                'preclassical'                          
number_of_logic_tree_samples    0                                       
maximum_distance                {'default': [(1.0, 50.0), (10.0, 50.0)]}
investigation_time              25.0                                    
ses_per_logic_tree_path         1                                       
truncation_level                3.0                                     
rupture_mesh_spacing            5.0                                     
complex_fault_mesh_spacing      5.0                                     
width_of_mfd_bin                0.3                                     
area_source_discretization      20.0                                    
pointsource_distance            None                                    
ground_motion_correlation_model 'JB2009'                                
minimum_intensity               {}                                      
random_seed                     23                                      
master_seed                     0                                       
ses_seed                        42                                      
=============================== ========================================

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
====== =================== ====
grp_id gsim                rlzs
====== =================== ====
0      '[ZhaoEtAl2006Asc]' [0] 
====== =================== ====

Required parameters per tectonic region type
--------------------------------------------
===== =================== ========= ========== ===================
et_id gsims               distances siteparams ruptparams         
===== =================== ========= ========== ===================
0     '[ZhaoEtAl2006Asc]' rrup      vs30       hypo_depth mag rake
===== =================== ========= ========== ===================

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         A    1.519E-04 41        120         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    1.519E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       1      5.856E-04 nan    5.856E-04 5.856E-04
read_source_model  1      0.00379   nan    0.00379   0.00379  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      1.72 KB 
preclassical           239 B   
================= ==== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_47289, maxmem=0.3 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.07309   0.0       1     
composite source model    0.06056   0.0       1     
total read_source_model   0.00379   0.0       1     
total preclassical        5.856E-04 0.0       1     
========================= ========= ========= ======