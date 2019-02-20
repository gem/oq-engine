Event Based Risk QA Test 2
==========================

============== ===================
checksum32     318,101,501        
date           2019-02-18T08:37:11
engine_version 3.4.0-git9883ae17a5
============== ===================

num_sites = 3, num_levels = 15

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

  <RlzsAssoc(size=1, rlzs=1)
  0,'[ChiouYoungs2008]': [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 18           18          
================ ====== ==================== ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
4 asset(s) x 1 realization(s) x 1 loss type(s) x 2 losses x 8 bytes x 30 tasks = 1.88 KB

Exposure model
--------------
=============== ========
#assets         4       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ======= === === ========= ==========
taxonomy mean    stddev  min max num_sites num_assets
RM       1.00000 0.0     1   1   2         2         
RC+      1.00000 NaN     1   1   1         1         
W/1      1.00000 NaN     1   1   1         1         
*ALL*    1.33333 0.57735 1   2   3         4         
======== ======= ======= === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      1         P    0     1     6            0.00227   0.0        1.00000   1         4.00000
0      3         P    2     3     6            0.00206   0.0        1.00000   1         8.00000
0      2         P    1     2     6            0.00201   0.0        1.00000   1         2.00000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.00634   3     
==== ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =======
operation-duration mean      stddev    min       max       outputs
read_source_models 0.00343   NaN       0.00343   0.00343   1      
only_filter        0.00280   NaN       0.00280   0.00280   1      
sample_ruptures    0.00935   NaN       0.00935   0.00935   1      
get_eid_rlz        5.616E-04 1.343E-04 4.363E-04 7.801E-04 8      
================== ========= ========= ========= ========= =======

Data transfer
-------------
================== ============================================= ========
task               sent                                          received
read_source_models converter=313 B fnames=113 B                  2.27 KB 
only_filter        srcs=1.91 KB srcfilter=253 B dummy=14 B       2.09 KB 
sample_ruptures    param=3.27 KB sources=2.14 KB srcfilter=220 B 1.94 KB 
get_eid_rlz        self=11.61 KB                                 2.15 KB 
================== ============================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total sample_ruptures    0.00935  1.28516   1     
iter_ruptures            0.00614  0.0       3     
saving ruptures          0.00478  0.0       1     
total get_eid_rlz        0.00449  0.23047   8     
total read_source_models 0.00343  0.0       1     
total only_filter        0.00280  1.40625   1     
store source_info        0.00197  0.0       1     
reading exposure         0.00162  0.0       1     
store source model       0.00145  0.0       1     
======================== ======== ========= ======