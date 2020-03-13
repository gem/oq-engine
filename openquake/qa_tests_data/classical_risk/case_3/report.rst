Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     2_395_394_634      
date           2020-03-13T11:20:10
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 12, num_levels = 19, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== =========== ======================= =================
grp_id gsims               distances   siteparams              ruptparams       
====== =================== =========== ======================= =================
0      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================== =========== ======================= =================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.42579   33_831       1_846       
====== ========= ============ ============

Exposure model
--------------
=========== ==
#assets     13
#taxonomies 4 
=========== ==

======== ======= ======= === === ========= ==========
taxonomy mean    stddev  min max num_sites num_assets
W        1.00000 0.0     1   1   5         5         
A        1.00000 0.0     1   1   4         4         
DS       2.00000 NaN     2   2   1         2         
UFB      1.00000 0.0     1   1   2         2         
*ALL*    1.08333 0.28868 1   2   12        13        
======== ======= ======= === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
232       0      A    1_612        0.01674   0.46526   1_612       
225       0      A    520          0.00208   0.15385   234         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.01883  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.10767 0.11154 0.01933 0.39365 14     
read_source_model  0.98455 NaN     0.98455 0.98455 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ============================================== ========
task              sent                                           received
read_source_model                                                13.36 KB
preclassical      srcs=28.95 KB params=10.5 KB srcfilter=3.05 KB 4.53 KB 
================= ============================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66857                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          1.50738   1.78906   14    
splitting/filtering sources 1.18955   0.65625   14    
composite source model      0.99672   0.28516   1     
total read_source_model     0.98455   0.13672   1     
store source_info           0.00222   0.0       1     
aggregate curves            6.053E-04 0.0       2     
reading exposure            5.910E-04 0.0       1     
=========================== ========= ========= ======