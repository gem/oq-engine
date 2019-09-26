Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     39,734,555         
date           2019-09-24T15:21:07
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 13, num_levels = 91, num_rlzs = 8

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              10.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     323               
master_seed                     42                
ses_seed                        323               
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure.xml <exposure.xml>`_                                            
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                              
job_ini                  `job.ini <job.ini>`_                                                      
site_model               `site_model.xml <site_model.xml>`_                                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
======================== ======= ====================== ================
smlt_path                weight  gsim_logic_tree        num_realizations
======================== ======= ====================== ================
AreaSource               0.50000 simple(4,0,0,0,0,0,0)  4               
FaultSourceAndBackground 0.20000 simple(4,0,0,0,0,0,0)  4               
SeiFaCrust               0.30000 trivial(0,0,0,0,0,0,0) 0               
======================== ======= ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================== ================= ======================= ============================
grp_id gsims                                                                              distances         siteparams              ruptparams                  
====== ================================================================================== ================= ======================= ============================
0      '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
1      '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
2      '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
====== ================================================================================== ================= ======================= ============================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=32, rlzs=8)>

Number of ruptures per tectonic region type
-------------------------------------------
===================== ====== ==================== ============ ============
source_model          grp_id trt                  eff_ruptures tot_ruptures
===================== ====== ==================== ============ ============
../src/as_model.xml   0      Active Shallow Crust 6            2,982       
../src/fsbg_model.xml 1      Active Shallow Crust 1            108         
===================== ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 7    
#tot_ruptures 3,099
============= =====

Estimated data transfer for the avglosses
-----------------------------------------
14 asset(s) x 8 realization(s) x 1 loss type(s) losses x 8 bytes x 64 tasks = 56 KB

Exposure model
--------------
=========== ==
#assets     14
#taxonomies 9 
=========== ==

======== ======= ======= === === ========= ==========
taxonomy mean    stddev  min max num_sites num_assets
RC_LR    1.00000 0.0     1   1   3         3         
RC_MR    1.00000 NaN     1   1   1         1         
RC_HR    1.00000 NaN     1   1   1         1         
URM_1S   1.00000 0.0     1   1   2         2         
URM_2S   1.00000 0.0     1   1   2         2         
SAM_1S   1.00000 NaN     1   1   1         1         
SAM_2S   1.00000 0.0     1   1   2         2         
SAM_3S   1.00000 NaN     1   1   1         1         
SAM_4S   1.00000 NaN     1   1   1         1         
*ALL*    0.16867 0.40783 0   2   83        14        
======== ======= ======= === === ========= ==========

Slowest sources
---------------
========== ====== ==== ============ ========= ========= ============ =====
source_id  grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========== ====== ==== ============ ========= ========= ============ =====
AS_TRAS334 0      A    760          0.04165   7.00000   4.00000      96   
AS_TRAS346 0      A    527          0.01964   5.00000   2.00000      101  
AS_TRAS458 0      A    399          0.01948   2.00000   2.00000      102  
AS_TRAS360 0      A    624          0.01769   3.00000   2.00000      113  
AS_TRAS395 0      A    432          0.01363   3.00000   2.00000      146  
AS_TRAS410 0      A    240          0.00545   2.00000   0.0          0.0  
========== ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.11754   7     
P    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ========= ======= =======
operation-duration mean    stddev  min       max     outputs
compute_gmfs       0.01966 0.00303 0.01388   0.02464 29     
read_source_models 0.02924 0.03932 0.00109   0.07417 3      
sample_ruptures    0.01591 0.00970 7.699E-04 0.03234 8      
================== ======= ======= ========= ======= =======

Data transfer
-------------
================== ===================================================== =========
task               sent                                                  received 
compute_gmfs       param=209.94 KB rupgetter=52.93 KB srcfilter=34.38 KB 219.57 KB
read_source_models converter=942 B fnames=362 B                          12.52 KB 
sample_ruptures    param=56.98 KB sources=17.25 KB srcfilter=9.48 KB     9.92 KB  
================== ===================================================== =========

Slowest operations
------------------
======================== ======== ========= ======
calc_1795                time_sec memory_mb counts
======================== ======== ========= ======
EventBasedCalculator.run 0.88974  2.03906   1     
total compute_gmfs       0.57022  1.32031   29    
building hazard          0.30733  0.41797   29    
getting ruptures         0.20489  1.32031   29    
total sample_ruptures    0.12732  0.32422   8     
total read_source_models 0.08772  0.0       3     
saving events            0.08531  0.0       1     
saving gmfs              0.03857  0.0       29    
building hazard curves   0.03139  0.0       236   
saving ruptures          0.01299  0.0       6     
aggregating hcurves      0.00856  0.0       29    
saving gmf_data/indices  0.00756  0.0       1     
store source_info        0.00291  0.0       1     
reading exposure         0.00222  0.0       1     
======================== ======== ========= ======