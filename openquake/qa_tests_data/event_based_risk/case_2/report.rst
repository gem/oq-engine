Event Based Risk QA Test 2
==========================

============== ===================
checksum32     1_772_081_114      
date           2020-03-13T11:21:59
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 3, num_levels = 3, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
investigation_time              50.0              
ses_per_logic_tree_path         20                
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
area_source_discretization      10.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     42                
ses_seed                        42                
=============================== ==================

Input files
-----------
======================== ==============================================================
Name                     File                                                          
======================== ==============================================================
exposure                 `exposure.xml <exposure.xml>`_                                
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                  
job_ini                  `job.ini <job.ini>`_                                          
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_  
structural_vulnerability `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_
======================== ==============================================================

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
0      0.16667   18           18          
====== ========= ============ ============

Exposure model
--------------
=========== =
#assets     4
#taxonomies 3
=========== =

======== ======= ======= === === ========= ==========
taxonomy mean    stddev  min max num_sites num_assets
RM       1.00000 0.0     1   1   2         2         
RC+      1.00000 NaN     1   1   1         1         
W/1      1.00000 NaN     1   1   1         1         
*ALL*    1.33333 0.57735 1   2   3         4         
======== ======= ======= === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      P    6            0.00306   0.16667   6.00000     
3         0      P    6            0.00302   0.16667   6.00000     
2         0      P    6            0.00299   0.16667   6.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00906  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.00429 9.742E-05 0.00420 0.00439 3      
read_source_model  0.00178 NaN       0.00178 0.00178 1      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================= =========================================== ========
task              sent                                        received
read_source_model                                             2.16 KB 
preclassical      srcs=3.41 KB params=2.27 KB srcfilter=669 B 1.08 KB 
================= =========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66968                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.01287   0.51172   3     
composite source model      0.01057   0.0       1     
store source_info           0.00213   0.0       1     
total read_source_model     0.00178   0.0       1     
reading exposure            0.00157   0.0       1     
splitting/filtering sources 0.00118   0.0       3     
aggregate curves            6.790E-04 0.0       3     
=========================== ========= ========= ======