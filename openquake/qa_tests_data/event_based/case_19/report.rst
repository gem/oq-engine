Vancouver - 5 branches - 5 Years
================================

============== ===================
checksum32     2_220_417_399      
date           2020-03-13T11:21:43
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 2, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ================================
calculation_mode                'preclassical'                  
number_of_logic_tree_samples    1                               
maximum_distance                {'default': 200.0}              
investigation_time              10.0                            
ses_per_logic_tree_path         1                               
truncation_level                3.0                             
rupture_mesh_spacing            10.0                            
complex_fault_mesh_spacing      10.0                            
width_of_mfd_bin                0.5                             
area_source_discretization      10.0                            
pointsource_distance            {'default': {}}                 
ground_motion_correlation_model None                            
minimum_intensity               {'SA(0.3)': 0.1, 'default': 0.1}
random_seed                     24                              
master_seed                     0                               
ses_seed                        23                              
=============================== ================================

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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b0        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================================================================================================================================== ========= ============ ==============
grp_id gsims                                                                                                                                                 distances siteparams   ruptparams    
====== ===================================================================================================================================================== ========= ============ ==============
0      "[NRCan15SiteTerm]\ngmpe_name = 'SInterCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'SInterCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'SInterCan15Upp'" rrup      backarc vs30 hypo_depth mag
1      "[NRCan15SiteTerm]\ngmpe_name = 'SSlabCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'SSlabCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'SSlabCan15Upp'"    repi      vs30         hypo_depth mag
2      "[NRCan15SiteTerm]\ngmpe_name = 'SInterCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'SInterCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'SInterCan15Upp'" rrup      backarc vs30 hypo_depth mag
====== ===================================================================================================================================================== ========= ============ ==============

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.25000   42_533       8.00000     
1      0.02444   54_576       2_496       
2      0.07407   1_971        1_566       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
CIS-15    0      C    8            0.00714   0.25000   8.00000     
GTP       2      A    1_971        0.00625   0.07407   1_566       
JDFN      1      A    3_276        0.00339   0.02444   2_496       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00964  
C    0.00714  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.13328 0.14502 0.00854 0.30428 5      
read_source_model  0.68509 NaN     0.68509 0.68509 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model                                            10.07 KB
preclassical      srcs=13.72 KB gsims=3.51 KB params=3.05 KB 1.72 KB 
================= ========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66954                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.70369   0.0       1     
total read_source_model     0.68509   0.0       1     
total preclassical          0.66638   0.0       5     
splitting/filtering sources 0.54771   0.0       5     
store source_info           0.00249   0.0       1     
aggregate curves            8.919E-04 0.0       3     
=========================== ========= ========= ======