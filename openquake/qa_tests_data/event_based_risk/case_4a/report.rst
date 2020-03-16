Event Based Hazard
==================

============== ===================
checksum32     2_621_435_700      
date           2020-03-13T11:21:47
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         100               
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     24                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                                
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                              
job_ini                  `job_hazard.ini <job_hazard.ini>`_                                        
site_model               `site_model.xml <site_model.xml>`_                                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

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
0      0.03313   483          483         
====== ========= ============ ============

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
Wood     1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
3         0      S    482          0.03096   0.03112   482         
1         0      X    1            0.00292   1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.03096  
X    0.00292  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.01847 0.02015 0.00422 0.03272 2      
read_source_model  0.01162 NaN     0.01162 0.01162 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ============================================ ========
task              sent                                         received
read_source_model                                              11.76 KB
preclassical      srcs=14.23 KB params=1.21 KB srcfilter=446 B 739 B   
================= ============================================ ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66958                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.03694   0.85547   2     
composite source model      0.02532   0.0       1     
total read_source_model     0.01162   0.0       1     
store source_info           0.00219   0.0       1     
splitting/filtering sources 0.00126   0.28906   2     
reading exposure            6.814E-04 0.0       1     
aggregate curves            5.295E-04 0.0       2     
=========================== ========= ========= ======