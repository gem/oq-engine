Vancouver - 5 branches - 5 Years
================================

============== ====================
checksum32     3_162_001_059       
date           2020-11-02T09:36:30 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 2, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ======================================
calculation_mode                'preclassical'                        
number_of_logic_tree_samples    1                                     
maximum_distance                {'default': [(1.0, 200), (10.0, 200)]}
investigation_time              10.0                                  
ses_per_logic_tree_path         1                                     
truncation_level                3.0                                   
rupture_mesh_spacing            10.0                                  
complex_fault_mesh_spacing      10.0                                  
width_of_mfd_bin                0.5                                   
area_source_discretization      10.0                                  
pointsource_distance            None                                  
ground_motion_correlation_model None                                  
minimum_intensity               {'SA(0.3)': 0.1, 'default': 0.1}      
random_seed                     24                                    
master_seed                     0                                     
ses_seed                        23                                    
=============================== ======================================

Input files
-----------
======================= ==============================================
Name                    File                                          
======================= ==============================================
gsim_logic_tree         `gmmLT_analytical.xml <gmmLT_analytical.xml>`_
job_ini                 `job.ini <job.ini>`_                          
site_model              `Vs30_Vancouver.xml <Vs30_Vancouver.xml>`_    
source_model_logic_tree `ssmLT_0.xml <ssmLT_0.xml>`_                  
======================= ==============================================

Composite source model
----------------------
====== ================================================= ====
grp_id gsim                                              rlzs
====== ================================================= ====
0      "[NRCan15SiteTerm]\ngmpe_name = 'SInterCan15Mid'" [0] 
1      "[NRCan15SiteTerm]\ngmpe_name = 'SInterCan15Upp'" [0] 
2      "[NRCan15SiteTerm]\ngmpe_name = 'SSlabCan15Mid'"  [0] 
====== ================================================= ====

Required parameters per tectonic region type
--------------------------------------------
===== ===================================================================================================================================================== ========= ============ ==============
et_id gsims                                                                                                                                                 distances siteparams   ruptparams    
===== ===================================================================================================================================================== ========= ============ ==============
0     "[NRCan15SiteTerm]\ngmpe_name = 'SInterCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'SInterCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'SInterCan15Upp'" rrup      backarc vs30 hypo_depth mag
1     "[NRCan15SiteTerm]\ngmpe_name = 'SSlabCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'SSlabCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'SSlabCan15Upp'"    repi      vs30         hypo_depth mag
2     "[NRCan15SiteTerm]\ngmpe_name = 'SInterCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'SInterCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'SInterCan15Upp'" rrup      backarc vs30 hypo_depth mag
===== ===================================================================================================================================================== ========= ============ ==============

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
CIS-15    C    0.00261   2         8           
JDFN      A    1.605E-04 2         3_276       
GTP       A    1.447E-04 2         1_971       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    3.052E-04
C    0.00261  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       5      0.00112 88%    5.879E-04 0.00311
read_source_model  1      0.01018 nan    0.01018   0.01018
================== ====== ======= ====== ========= =======

Data transfer
-------------
================= ================================ ========
task              sent                             received
read_source_model                                  7.23 KB 
preclassical      srcfilter=14.77 KB srcs=13.92 KB 1.09 KB 
================= ================================ ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47304, maxmem=1.2 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.42249  0.0       1     
composite source model    1.41470  0.0       1     
total read_source_model   0.01018  0.0       1     
total preclassical        0.00559  0.46484   5     
========================= ======== ========= ======