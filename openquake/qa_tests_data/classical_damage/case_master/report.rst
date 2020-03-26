classical damage hazard
=======================

============== ===================
checksum32     1_953_095_324      
date           2020-03-13T11:20:46
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 7, num_levels = 90, num_rlzs = 8

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     24                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ========================================================================
Name                    File                                                                    
======================= ========================================================================
contents_fragility      `contents_fragility_model.xml <contents_fragility_model.xml>`_          
exposure                `exposure_model.xml <exposure_model.xml>`_                              
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                            
job_ini                 `job_haz.ini <job_haz.ini>`_                                            
nonstructural_fragility `nonstructural_fragility_model.xml <nonstructural_fragility_model.xml>`_
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_            
structural_fragility    `structural_fragility_model.xml <structural_fragility_model.xml>`_      
======================= ========================================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        0.25000 4               
b2        0.75000 4               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= =========== ======================= =================
grp_id gsims                                     distances   siteparams              ruptparams       
====== ========================================= =========== ======================= =================
0      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[AkkarBommer2010]' '[ChiouYoungs2008]'   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      '[AkkarBommer2010]' '[ChiouYoungs2008]'   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ========================================= =========== ======================= =================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.21784   482          482         
2      1.75000   4            4.00000     
3      7.00000   1            1.00000     
====== ========= ============ ============

Exposure model
--------------
=========== =
#assets     7
#taxonomies 3
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   4         4         
tax2     1.00000 0.0    1   1   2         2         
tax3     1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      S    482          0.02453   0.21784   482         
2         2      S    4            0.00336   1.75000   4.00000     
2         3      X    1            8.941E-05 7.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.02789  
X    8.941E-05
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.01490 0.01519 0.00416 0.02564 2      
read_source_model  0.01674 0.00658 0.01209 0.02139 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model converter=664 B fname=220 B srcfilter=8 B 13.82 KB
preclassical      srcs=15.17 KB params=2.89 KB gsims=538 B  789 B   
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66914                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.08310   0.08203   1     
total read_source_model     0.03349   0.0       2     
total preclassical          0.02980   1.13281   2     
store source_info           0.00223   0.0       1     
aggregate curves            6.242E-04 0.0       2     
splitting/filtering sources 6.104E-04 0.0       2     
reading exposure            5.403E-04 0.0       1     
=========================== ========= ========= ======