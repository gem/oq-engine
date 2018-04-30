Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     3,253,033,277      
date           2018-04-30T11:21:39
engine_version 3.1.0-gitb0812f0   
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
SeiFaCrust               0.30000 simple(4,0,0,0,0,0,0) 0/0             
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
AS_TRAS334   AreaSource   2,280        1.44651   0.01898    308       38        49    
AS_TRAS360   AreaSource   1,872        0.91277   0.00887    132       39        102   
AS_TRAS395   AreaSource   1,296        0.78730   0.00713    109       27        72    
AS_TRAS346   AreaSource   1,581        0.70398   0.01361    128       31        45    
AS_TRAS458   AreaSource   1,197        0.58516   0.01537    46        21        39    
AS_TRAS410   AreaSource   720          0.42469   0.00363    84        12        1     
FSBG_TRBG989 AreaSource   324          0.14148   0.00498    14        8         12    
100041       PointSource  27           0.0       3.576E-06  0         0         0     
============ ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   5.00190   7     
PointSource  0.0       1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
compute_ruptures   0.52659 0.19319 0.14417 0.69573 11       
================== ======= ======= ======= ======= =========

Informational data
------------------
================ ================================================================================== ========
task             sent                                                                               received
compute_ruptures sources=104.18 KB src_filter=15.26 KB param=14.62 KB gsims=4.19 KB monitor=3.54 KB 61.7 KB 
================ ================================================================================== ========

Slowest operations
------------------
============================== ======== ========= ======
operation                      time_sec memory_mb counts
============================== ======== ========= ======
total compute_ruptures         5.79247  4.87500   11    
managing sources               0.73515  0.0       1     
reading composite source model 0.09026  0.0       1     
reading site collection        0.08789  0.0       1     
splitting sources              0.07323  0.0       1     
store source_info              0.04296  0.0       1     
making contexts                0.03393  0.0       31    
saving ruptures                0.02366  0.0       11    
reading exposure               0.00342  0.0       1     
unpickling compute_ruptures    0.00293  0.0       11    
setting event years            0.00138  0.0       1     
============================== ======== ========= ======