British Columbia With Vs30
==========================

============== ====================
checksum32     2_694_571_962       
date           2020-11-02T09:36:15 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 2, num_levels = 3, num_rlzs = 15

Parameters
----------
=============================== ============================================================================================
calculation_mode                'preclassical'                                                                              
number_of_logic_tree_samples    0                                                                                           
maximum_distance                {'Active Shallow Offshore': [(1.0, 800), (10.0, 800)], 'default': [(1.0, 800), (10.0, 800)]}
investigation_time              20.0                                                                                        
ses_per_logic_tree_path         1                                                                                           
truncation_level                3.0                                                                                         
rupture_mesh_spacing            5.0                                                                                         
complex_fault_mesh_spacing      10.0                                                                                        
width_of_mfd_bin                0.1                                                                                         
area_source_discretization      15.0                                                                                        
pointsource_distance            None                                                                                        
ground_motion_correlation_model None                                                                                        
minimum_intensity               {'SA(0.3)': 0.001, 'SA(0.6)': 0.001, 'SA(1.0)': 0.001, 'default': 0.001}                    
random_seed                     24                                                                                          
master_seed                     0                                                                                           
ses_seed                        23                                                                                          
=============================== ============================================================================================

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
====== ================================================== ==========
grp_id gsim                                               rlzs      
====== ================================================== ==========
0      "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Low'" [0, 6, 9] 
0      "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Mid'" [1, 7, 10]
0      "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Upp'" [2, 8, 11]
1      "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Low'" [3, 12]   
1      "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Mid'" [4, 13]   
1      "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Upp'" [5, 14]   
====== ================================================== ==========

Required parameters per tectonic region type
--------------------------------------------
===== ======================================================================================================================================================== ========= ========== ==========
et_id gsims                                                                                                                                                    distances siteparams ruptparams
===== ======================================================================================================================================================== ========= ========== ==========
0     "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Upp'" repi      vs30       mag rake  
1     "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Upp'" repi      vs30       mag rake  
2     "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Upp'" repi      vs30       mag rake  
3     "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Upp'" repi      vs30       mag rake  
4     "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Low'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Mid'" "[NRCan15SiteTerm]\ngmpe_name = 'OceanicCan15Upp'" repi      vs30       mag rake  
===== ======================================================================================================================================================== ========= ========== ==========

Exposure model
--------------
=========== =
#assets     2
#taxonomies 2
=========== =

========== ========== ======= ====== === === =========
taxonomy   num_assets mean    stddev min max num_sites
RES1-W1-HC 1          1.00000 nan    1   1   1        
RES1-W1-LC 1          1.00000 nan    1   1   1        
*ALL*      9          0.22222 187%   0   1   2        
========== ========== ======= ====== === === =========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
OFS;0     A    1.392E-04 2         8_778       
OFS;1     A    1.373E-04 2         15_618      
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    2.766E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       2      6.310E-04 5%     5.977E-04 6.642E-04
read_source_model  5      0.00332   39%    0.00249   0.00591  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ============================== ========
task              sent                           received
read_source_model converter=1.83 KB fname=535 B  10.45 KB
preclassical      srcs=5.14 KB srcfilter=2.68 KB 486 B   
================= ============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47292, maxmem=1.2 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.29149  0.0       1     
composite source model    1.26695  0.0       1     
total read_source_model   0.01658  0.47266   5     
reading exposure          0.00186  0.0       1     
total preclassical        0.00126  0.36328   2     
========================= ======== ========= ======