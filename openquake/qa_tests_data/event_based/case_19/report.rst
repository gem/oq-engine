Vancouver - 5 branches - 5 Years
================================

============== ====================
checksum32     3_162_001_059       
date           2020-11-02T09:14:04 
engine_version 3.11.0-git24d6ba92cd
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
CIS-15    C    0.00259   2         8           
GTP       A    1.385E-04 2         1_971       
JDFN      A    1.316E-04 2         3_276       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    2.701E-04
C    0.00259  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       5      0.00112 88%    5.913E-04 0.00310
read_source_model  1      0.01016 nan    0.01016   0.01016
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
calc_46960, maxmem=1.2 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.50752  0.0       1     
composite source model    1.49989  0.0       1     
total read_source_model   0.01016  0.0       1     
total preclassical        0.00560  0.41797   5     
========================= ======== ========= ======