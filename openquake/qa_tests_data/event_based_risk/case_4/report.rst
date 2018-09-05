Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     3,454,425,156      
date           2018-09-05T10:04:20
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 14, num_levels = 91

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
source                   `as_model.xml <as_model.xml>`_                                            
source                   `fsbg_model.xml <fsbg_model.xml>`_                                        
source                   `ss_model.xml <ss_model.xml>`_                                            
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
======================== ======= ===================== ================
smlt_path                weight  gsim_logic_tree       num_realizations
======================== ======= ===================== ================
AreaSource               0.50000 simple(4,0,0,0,0,0,0) 4/4             
FaultSourceAndBackground 0.20000 simple(4,0,0,0,0,0,0) 4/4             
SeiFaCrust               0.30000 simple(4,0,0,0,0,0,0) 0/4             
======================== ======= ===================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================== ================= ======================= ============================
grp_id gsims                                                                      distances         siteparams              ruptparams                  
====== ========================================================================== ================= ======================= ============================
0      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
1      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
2      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
====== ========================================================================== ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,AkkarBommer2010(): [0]
  0,CauzziFaccioli2008(): [1]
  0,ChiouYoungs2008(): [2]
  0,ZhaoEtAl2006Asc(): [3]
  1,AkkarBommer2010(): [4]
  1,CauzziFaccioli2008(): [5]
  1,ChiouYoungs2008(): [6]
  1,ZhaoEtAl2006Asc(): [7]>

Number of ruptures per tectonic region type
-------------------------------------------
===================== ====== ==================== ============ ============
source_model          grp_id trt                  eff_ruptures tot_ruptures
===================== ====== ==================== ============ ============
../src/as_model.xml   0      Active Shallow Crust 8,946        8,946       
../src/fsbg_model.xml 1      Active Shallow Crust 216          324         
===================== ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 9,162
#tot_ruptures 9,297
#tot_weight   0    
============= =====

Estimated data transfer for the avglosses
-----------------------------------------
14 asset(s) x 8 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 64 tasks = 56 KB

Exposure model
--------------
=============== ========
#assets         14      
#taxonomies     9       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
RC_LR    1.00000 0.0    1   1   3         3         
RC_MR    1.00000 NaN    1   1   1         1         
RC_HR    1.00000 NaN    1   1   1         1         
URM_1S   1.00000 0.0    1   1   2         2         
URM_2S   1.00000 0.0    1   1   2         2         
SAM_1S   1.00000 NaN    1   1   1         1         
SAM_2S   1.00000 0.0    1   1   2         2         
SAM_3S   1.00000 NaN    1   1   1         1         
SAM_4S   1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   14        14        
======== ======= ====== === === ========= ==========

Slowest sources
---------------
============ ============ ============ ========= ========== ========= ========= ======
source_id    source_class num_ruptures calc_time split_time num_sites num_split events
============ ============ ============ ========= ========== ========= ========= ======
AS_TRAS334   AreaSource   2,280        2.10729   0.01771    8.10526   38        9     
AS_TRAS360   AreaSource   1,872        1.68104   0.00720    3.38462   39        9     
AS_TRAS346   AreaSource   1,581        1.37141   0.01235    4.12903   31        1     
AS_TRAS395   AreaSource   1,296        1.08758   0.00605    4.03704   27        5     
AS_TRAS458   AreaSource   1,197        0.94179   0.01263    2.19048   21        3     
AS_TRAS410   AreaSource   720          0.57693   0.00293    7.00000   12        1     
FSBG_TRBG989 AreaSource   324          0.15101   0.00400    1.75000   8         2     
100041       PointSource  27           0.0       2.861E-06  0.0       0         0     
============ ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   7.91704   7     
PointSource  0.0       1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ======= ========= ======= =========
operation-duration   mean    stddev  min       max     num_tasks
pickle_source_models 0.03220 0.04173 0.00244   0.07989 3        
preprocess           0.10717 0.02720 7.489E-04 0.19012 78       
compute_gmfs         0.08625 0.09601 0.02776   0.19706 3        
==================== ======= ======= ========= ======= =========

Data transfer
-------------
==================== ================================================================================================= =========
task                 sent                                                                                              received 
pickle_source_models monitor=1.01 KB converter=867 B fnames=587 B                                                      499 B    
preprocess           srcs=184.82 KB param=123.7 KB monitor=27.19 KB srcfilter=19.27 KB                                 254.11 KB
compute_gmfs         sources_or_ruptures=74.68 KB param=20.38 KB rlzs_by_gsim=1.92 KB monitor=1.01 KB src_filter=660 B 93.15 KB 
==================== ================================================================================================= =========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total preprocess           8.35912   0.03516   78    
total compute_gmfs         0.25875   0.0       3     
building hazard            0.23748   0.0       3     
total pickle_source_models 0.09660   0.0       3     
saving ruptures            0.06956   0.0       28    
splitting sources          0.06358   0.0       1     
making contexts            0.04265   0.0       31    
store source_info          0.03387   0.0       1     
building ruptures          0.00796   0.0       3     
managing sources           0.00778   0.0       1     
building hazard curves     0.00595   0.0       44    
saving gmfs                0.00586   0.0       3     
saving gmf_data/indices    0.00569   0.0       1     
GmfGetter.init             0.00424   0.0       3     
aggregating hcurves        0.00200   0.0       3     
setting event years        0.00133   0.0       1     
reading exposure           5.121E-04 0.0       1     
========================== ========= ========= ======