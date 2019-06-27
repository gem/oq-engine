Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     39,734,555         
date           2019-06-24T15:33:54
engine_version 3.6.0-git4b6205639c
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
../src/as_model.xml   0      Active Shallow Crust 2,982        2,982       
../src/fsbg_model.xml 1      Active Shallow Crust 108          108         
===================== ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 3,090
#tot_ruptures 3,099
#tot_weight   3,099
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
====== ============ ==== ===== ===== ============ ========= ========= ======= =============
grp_id source_id    code gidx1 gidx2 num_ruptures calc_time num_sites weight  checksum     
====== ============ ==== ===== ===== ============ ========= ========= ======= =============
0      AS_TRAS334   A    0     23    760          0.02787   0.0       2.00000 2,711,824,330
0      AS_TRAS346   A    23    36    527          0.02046   0.0       2.00000 3,619,258,796
0      AS_TRAS458   A    61    67    399          0.01819   0.0       2.00000 3,909,105,536
0      AS_TRAS360   A    36    44    624          0.01678   0.0       2.00000 1,804,745,429
0      AS_TRAS395   A    44    52    432          0.01521   0.0       2.00000 3,205,773,375
0      AS_TRAS410   A    52    61    240          0.00661   0.0       0.0     1,437,748,624
1      FSBG_TRBG989 A    67    74    108          0.00503   0.0       2.00000 1,922,238,106
2      100041       P    74    75    9            0.0       0.0       0.0     1,039,891,805
====== ============ ==== ===== ===== ============ ========= ========= ======= =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.11016   7     
P    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =======
operation-duration mean      stddev    min       max       outputs
get_eid_rlz        6.375E-04 1.863E-04 3.104E-04 8.864E-04 29     
read_source_models 0.03004   0.03951   0.00176   0.07518   3      
sample_ruptures    0.01671   0.00971   0.00273   0.03210   8      
================== ========= ========= ========= ========= =======

Data transfer
-------------
================== ================================================ ========
task               sent                                             received
get_eid_rlz        self=55.31 KB                                    8.21 KB 
read_source_models converter=939 B fnames=362 B                     12.52 KB
sample_ruptures    param=56.98 KB sources=17.2 KB srcfilter=1.72 KB 9.67 KB 
================== ================================================ ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total sample_ruptures    0.13370  0.0       8     
total read_source_models 0.09012  0.0       3     
total get_eid_rlz        0.01849  0.0       29    
saving ruptures          0.01228  0.0       6     
store source model       0.00723  0.0       3     
reading exposure         0.00188  0.0       1     
store source_info        0.00178  0.0       1     
======================== ======== ========= ======