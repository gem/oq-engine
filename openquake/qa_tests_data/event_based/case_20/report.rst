British Columbia With Vs30
==========================

============== ===================
checksum32     749_403_350        
date           2020-03-13T11:21:29
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 2, num_levels = 3, num_rlzs = 15

Parameters
----------
=============================== ========================================================================
calculation_mode                'preclassical'                                                          
number_of_logic_tree_samples    0                                                                       
maximum_distance                {'default': 800.0, 'Active Shallow Offshore': 800.0}                    
investigation_time              20.0                                                                    
ses_per_logic_tree_path         1                                                                       
truncation_level                3.0                                                                     
rupture_mesh_spacing            5.0                                                                     
complex_fault_mesh_spacing      10.0                                                                    
width_of_mfd_bin                0.1                                                                     
area_source_discretization      15.0                                                                    
pointsource_distance            {'default': {}}                                                         
ground_motion_correlation_model None                                                                    
minimum_intensity               {'SA(0.3)': 0.001, 'SA(0.6)': 0.001, 'SA(1.0)': 0.001, 'default': 0.001}
random_seed                     24                                                                      
master_seed                     0                                                                       
ses_seed                        23                                                                      
=============================== ========================================================================

Input files
-----------
======================= =====================================================
Name                    File                                                 
======================= =====================================================
exposure                `BC_Exposure.xml <BC_Exposure.xml>`_                 
gsim_logic_tree         `gmmLT_analytical.xml <gmmLT_analytical.xml>`_       
job_ini                 `job.ini <job.ini>`_                                 
site_model              `vs30_a.xml <vs30_a.xml>`_ `vs30_b.xml <vs30_b.xml>`_
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_                             
======================= =====================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        0.24000 3               
b2        0.12000 3               
b3        0.24000 3               
b4        0.24000 3               
b5        0.16000 3               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================================================================================================================== ========= ========== ==========
grp_id gsims                                                                                                                                                    distances siteparams ruptparams
====== ======================================================================================================================================================== ========= ========== ==========
0      "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Upp'" repi      vs30       mag rake  
1      "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Upp'" repi      vs30       mag rake  
2      "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Upp'" repi      vs30       mag rake  
3      "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Upp'" repi      vs30       mag rake  
4      "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Upp'" repi      vs30       mag rake  
====== ======================================================================================================================================================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.03395   8_778        8_778       
1      0.03419   15_618       15_618      
====== ========= ============ ============

Exposure model
--------------
=========== =
#assets     2
#taxonomies 2
=========== =

========== ======= ======= === === ========= ==========
taxonomy   mean    stddev  min max num_sites num_assets
RES1-W1-HC 1.00000 NaN     1   1   1         1         
RES1-W1-LC 1.00000 NaN     1   1   1         1         
*ALL*      0.22222 0.44096 0   1   9         2         
========== ======= ======= === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
OFS       1      A    15_618       0.02334   0.03419   15_618      
OFS       0      A    8_778        0.01297   0.03395   8_778       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.03631  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.07178 0.02906 0.05123 0.09233 2      
read_source_model  0.05406 0.01475 0.04279 0.07071 5      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ============================================ ========
task              sent                                         received
read_source_model converter=1.83 KB fname=535 B srcfilter=20 B 13.61 KB
preclassical      srcs=4.97 KB gsims=2.11 KB params=1.59 KB    760 B   
================= ============================================ ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66942                  time_sec  memory_mb counts
=========================== ========= ========= ======
total read_source_model     0.27032   0.60547   5     
total preclassical          0.14356   2.33594   2     
composite source model      0.12266   0.0       1     
splitting/filtering sources 0.10235   0.38672   2     
store source_info           0.00210   0.0       1     
reading exposure            0.00163   0.0       1     
aggregate curves            6.711E-04 0.0       2     
=========================== ========= ========= ======