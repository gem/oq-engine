Event Based Risk QA Test 1
==========================

============== ===================
checksum32     1,503,171,782      
date           2019-07-30T15:04:38
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 3, num_levels = 25, num_rlzs = 2

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
=========================== ====================================================================
Name                        File                                                                
=========================== ====================================================================
exposure                    `exposure1.xml <exposure1.xml>`_                                    
gsim_logic_tree             `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                        
job_ini                     `job.ini <job.ini>`_                                                
nonstructural_vulnerability `vulnerability_model_nonstco.xml <vulnerability_model_nonstco.xml>`_
source_model_logic_tree     `source_model_logic_tree.xml <source_model_logic_tree.xml>`_        
structural_vulnerability    `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_      
=========================== ====================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(2)       2               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================= =========== ======================= =================
grp_id gsims                                   distances   siteparams              ruptparams       
====== ======================================= =========== ======================= =================
0      '[AkkarBommer2010]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ======================================= =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=2)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3            18          
================ ====== ==================== ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
4 asset(s) x 2 realization(s) x 2 loss type(s) losses x 8 bytes x 8 tasks = 1 KB

Exposure model
--------------
=========== =
#assets     4
#taxonomies 3
=========== =

======== ======= ======= === === ========= ==========
taxonomy mean    stddev  min max num_sites num_assets
RM       1.00000 0.0     1   1   2         2         
RC       1.00000 NaN     1   1   1         1         
W        1.00000 NaN     1   1   1         1         
*ALL*    1.33333 0.57735 1   2   3         4         
======== ======= ======= === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ======= ======
source_id grp_id code num_ruptures calc_time num_sites weight  speed 
========= ====== ==== ============ ========= ========= ======= ======
1         0      P    6            0.00204   1.00000   4.00000 1,965 
2         0      P    6            0.00127   1.00000   2.00000 1,572 
3         0      P    6            7.548E-04 1.00000   8.00000 10,598
========= ====== ==== ============ ========= ========= ======= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.00406   3     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.00131 NaN    0.00131 0.00131 1      
sample_ruptures    0.00717 NaN    0.00717 0.00717 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ============================================= ========
task               sent                                          received
read_source_models converter=314 B fnames=106 B                  2.27 KB 
sample_ruptures    param=3.96 KB sources=1.94 KB srcfilter=220 B 1.96 KB 
================== ============================================= ========

Slowest operations
------------------
======================== ======== ========= ======
calc_15568               time_sec memory_mb counts
======================== ======== ========= ======
EventBasedCalculator.run 0.16969  0.76953   1     
saving events            0.01075  0.0       1     
total sample_ruptures    0.00717  0.0       1     
store source_info        0.00387  0.0       1     
saving ruptures          0.00332  0.0       1     
reading exposure         0.00197  0.0       1     
total read_source_models 0.00131  0.0       1     
======================== ======== ========= ======