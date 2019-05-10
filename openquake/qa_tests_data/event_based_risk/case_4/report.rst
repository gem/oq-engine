Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     39,734,555         
date           2019-05-10T05:07:30
engine_version 3.5.0-gitbaeb4c1e35
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

  <RlzsAssoc(size=8, rlzs=8)
  0,'[AkkarBommer2010]': [0]
  0,'[CauzziFaccioli2008]': [1]
  0,'[ChiouYoungs2008]': [2]
  0,'[ZhaoEtAl2006Asc]': [3]
  1,'[AkkarBommer2010]': [4]
  1,'[CauzziFaccioli2008]': [5]
  1,'[ChiouYoungs2008]': [6]
  1,'[ZhaoEtAl2006Asc]': [7]>

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
#tot_weight   309  
============= =====

Estimated data transfer for the avglosses
-----------------------------------------
14 asset(s) x 8 realization(s) x 1 loss type(s) losses x 8 bytes x 64 tasks = 56 KB

Exposure model
--------------
=============== ========
#assets         14      
#taxonomies     9       
deductibile     absolute
insurance_limit absolute
=============== ========

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
*ALL*    1.07692 0.27735 1   2   13        14        
======== ======= ======= === === ========= ==========

Slowest sources
---------------
====== ============ ==== ===== ===== ============ ========= ========= =======
grp_id source_id    code gidx1 gidx2 num_ruptures calc_time num_sites weight 
====== ============ ==== ===== ===== ============ ========= ========= =======
0      AS_TRAS334   A    0     23    760          0.24509   0.0       2.00000
0      AS_TRAS360   A    36    44    624          0.18390   0.0       2.00000
0      AS_TRAS346   A    23    36    527          0.15949   0.0       2.00000
0      AS_TRAS395   A    44    52    432          0.13017   0.0       2.00000
0      AS_TRAS458   A    61    67    399          0.11832   0.0       2.00000
0      AS_TRAS410   A    52    61    240          0.07334   0.0       0.0    
1      FSBG_TRBG989 A    67    74    108          0.03173   0.0       2.00000
2      100041       P    74    75    9            0.0       0.0       0.0    
====== ============ ==== ===== ===== ============ ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.94202   7     
P    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ======= =======
operation-duration mean      stddev    min       max     outputs
read_source_models 0.02881   0.03900   7.863E-04 0.07335 3      
sample_ruptures    0.12091   0.08169   0.00169   0.24885 8      
get_eid_rlz        7.894E-04 5.034E-04 3.352E-04 0.00262 29     
================== ========= ========= ========= ======= =======

Data transfer
-------------
================== ================================================= ========
task               sent                                              received
read_source_models converter=939 B fnames=362 B                      12.5 KB 
sample_ruptures    param=56.98 KB sources=17.07 KB srcfilter=1.71 KB 9.56 KB 
get_eid_rlz        self=54.6 KB                                      8.21 KB 
================== ================================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total sample_ruptures    0.96724  1.07031   8     
iter_ruptures            0.93709  0.0       7     
total read_source_models 0.08642  0.0       3     
total get_eid_rlz        0.02289  0.0       29    
saving ruptures          0.02111  0.0       6     
store source model       0.00578  0.0       3     
store source_info        0.00184  0.0       1     
reading exposure         0.00159  0.0       1     
======================== ======== ========= ======