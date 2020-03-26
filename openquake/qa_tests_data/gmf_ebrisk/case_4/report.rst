event based two source models
=============================

============== ===================
checksum32     3_947_576_948      
date           2020-03-13T11:20:13
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 30, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         2                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model 'JB2009'          
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
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                              
job_ini                  `job_haz.ini <job_haz.ini>`_                                              
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        0.25000 1               
b2        0.75000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
1      '[BooreAtkinson2008]' rjb       vs30       mag rake  
2      '[AkkarBommer2010]'   rjb       vs30       mag rake  
3      '[AkkarBommer2010]'   rjb       vs30       mag rake  
====== ===================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.03112   482          482         
2      0.25000   4            4.00000     
3      1.00000   1            1.00000     
====== ========= ============ ============

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      S    482          0.02529   0.03112   482         
2         2      S    4            0.00325   0.25000   4.00000     
2         3      X    1            8.750E-05 1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.02854  
X    8.750E-05
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.01524 0.01579 0.00407 0.02640 2      
read_source_model  0.01768 0.00635 0.01318 0.02217 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ============================================ ========
task              sent                                         received
read_source_model converter=664 B fname=198 B srcfilter=8 B    13.8 KB 
preclassical      srcs=15.17 KB params=1.67 KB srcfilter=446 B 789 B   
================= ============================================ ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66859                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.07965   0.05078   1     
total read_source_model     0.03535   0.28516   2     
total preclassical          0.03048   1.54688   2     
store source_info           0.00216   0.0       1     
aggregate curves            7.234E-04 0.0       2     
splitting/filtering sources 6.423E-04 0.0       2     
reading exposure            5.519E-04 0.0       1     
=========================== ========= ========= ======