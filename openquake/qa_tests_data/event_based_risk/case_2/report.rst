Event Based Risk QA Test 2
==========================

============== ===================
checksum32     1,772,081,114      
date           2019-10-01T06:09:12
engine_version 3.8.0-gite0871b5c35
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3.00000   18           14          
====== ========= ============ ============

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
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
1         0      P    6            0.00118   1.00000   4.00000      3,378 
2         0      P    6            0.00107   1.00000   2.00000      1,867 
3         0      P    6            7.570E-04 1.00000   8.00000      10,568
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.00301   3     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.00451 NaN    0.00451 0.00451 1      
sample_ruptures    0.00599 NaN    0.00599 0.00599 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
=============== ==== ========
task            sent received
SourceReader         4.57 KB 
sample_ruptures      2 KB    
=============== ==== ========

Slowest operations
------------------
======================== ======== ========= ======
calc_23218               time_sec memory_mb counts
======================== ======== ========= ======
EventBasedCalculator.run 0.09857  0.0       1     
composite source model   0.01402  0.0       1     
saving events            0.00800  0.0       1     
store source_info        0.00798  0.0       1     
total sample_ruptures    0.00599  0.0       1     
saving ruptures          0.00491  0.0       1     
total SourceReader       0.00451  0.0       1     
reading exposure         0.00379  0.0       1     
======================== ======== ========= ======