Event Based Risk QA Test 2
==========================

============== ===================
checksum32     1,772,081,114      
date           2019-07-30T15:04:45
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 3, num_levels = 15, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
investigation_time              50.0              
ses_per_logic_tree_path         20                
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     42                
ses_seed                        42                
avg_losses                      True              
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== =========== ======================= =================
grp_id gsims               distances   siteparams              ruptparams       
====== =================== =========== ======================= =================
0      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================== =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3            18          
================ ====== ==================== ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
4 asset(s) x 1 realization(s) x 1 loss type(s) losses x 8 bytes x 8 tasks = 256 B

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
========= ====== ==== ============ ========= ========= ======= ======
source_id grp_id code num_ruptures calc_time num_sites weight  speed 
========= ====== ==== ============ ========= ========= ======= ======
1         0      P    6            0.00111   1.00000   4.00000 3,593 
2         0      P    6            0.00103   1.00000   2.00000 1,932 
3         0      P    6            6.943E-04 1.00000   8.00000 11,523
========= ====== ==== ============ ========= ========= ======= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.00284   3     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.00110 NaN    0.00110 0.00110 1      
sample_ruptures    0.00513 NaN    0.00513 0.00513 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ============================================= ========
task               sent                                          received
read_source_models converter=314 B fnames=106 B                  2.27 KB 
sample_ruptures    param=3.17 KB sources=1.94 KB srcfilter=220 B 1.96 KB 
================== ============================================= ========

Slowest operations
------------------
======================== ======== ========= ======
calc_15575               time_sec memory_mb counts
======================== ======== ========= ======
EventBasedCalculator.run 0.10802  0.25391   1     
saving events            0.00748  0.0       1     
total sample_ruptures    0.00513  0.0       1     
saving ruptures          0.00213  0.0       1     
store source_info        0.00208  0.0       1     
reading exposure         0.00167  0.0       1     
total read_source_models 0.00110  0.0       1     
======================== ======== ========= ======