Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     3,253,033,277      
date           2018-05-15T04:12:56
engine_version 3.1.0-git0acbc11   
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
#tot_ruptures 9,270
#tot_weight   929  
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
AS_TRAS334   PointSource  60           1.32135   0.0        308       38        49    
AS_TRAS360   PointSource  48           1.19477   0.0        132       39        102   
AS_TRAS346   PointSource  51           0.92133   0.0        128       31        45    
AS_TRAS395   PointSource  48           0.81647   0.0        109       27        72    
AS_TRAS458   PointSource  57           0.65030   0.0        46        21        39    
AS_TRAS410   PointSource  60           0.53850   0.0        84        12        1     
FSBG_TRBG989 PointSource  27           0.23916   0.0        14        8         12    
100041       PointSource  27           0.0       0.0        0         0         0     
============ ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  5.68188   8     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ========= ======= =========
operation-duration mean    stddev  min       max     num_tasks
prefilter          0.00498 0.00268 0.00179   0.01142 46       
compute_ruptures   0.47815 0.23312 9.332E-04 0.75406 12       
================== ======= ======= ========= ======= =========

Informational data
------------------
================ ================================================================================= =========
task             sent                                                                              received 
prefilter        srcs=140.01 KB monitor=14.51 KB srcfilter=10.29 KB                                146.08 KB
compute_ruptures sources=93.32 KB src_filter=16.66 KB param=15.95 KB gsims=4.57 KB monitor=3.87 KB 64.31 KB 
================ ================================================================================= =========

Slowest operations
------------------
============================== ======== ========= ======
operation                      time_sec memory_mb counts
============================== ======== ========= ======
total compute_ruptures         5.73779  1.16406   12    
managing sources               0.94420  0.0       1     
total prefilter                0.22918  3.37109   46    
reading composite source model 0.09414  0.0       1     
store source_info              0.08411  0.0       1     
splitting sources              0.07683  0.0       1     
making contexts                0.04194  0.0       31    
saving ruptures                0.02938  0.0       12    
reading site collection        0.01207  0.0       1     
unpickling prefilter           0.00616  0.0       46    
unpickling compute_ruptures    0.00438  0.0       12    
reading exposure               0.00191  0.0       1     
setting event years            0.00127  0.0       1     
============================== ======== ========= ======