Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     3,253,033,277      
date           2018-06-05T06:38:36
engine_version 3.2.0-git65c4735   
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
AS_TRAS334   AreaSource   2,280        1.37275   0.01971    8.10526   38        83    
AS_TRAS360   AreaSource   1,872        0.90197   0.00944    3.38462   39        72    
AS_TRAS346   AreaSource   1,581        0.75659   0.01434    4.12903   31        8     
AS_TRAS395   AreaSource   1,296        0.66966   0.00750    4.03704   27        60    
AS_TRAS458   AreaSource   1,197        0.60991   0.01622    2.19048   21        23    
AS_TRAS410   AreaSource   720          0.35848   0.00375    7.00000   12        20    
FSBG_TRBG989 AreaSource   324          0.11758   0.00530    1.75000   8         12    
100041       PointSource  27           0.0       3.338E-06  0.0       0         0     
============ ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   4.78693   7     
PointSource  0.0       1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00508 0.00210 0.00159 0.00953 46       
compute_ruptures   0.44499 0.15339 0.12538 0.63850 11       
================== ======= ======= ======= ======= =========

Data transfer
-------------
================ ================================================================================ =========
task             sent                                                                             received 
RtreeFilter      srcs=140.01 KB monitor=15.54 KB srcfilter=12.53 KB                               146.08 KB
compute_ruptures sources=124.34 KB param=14.82 KB gsims=4.19 KB monitor=3.79 KB src_filter=2.5 KB 60.65 KB 
================ ================================================================================ =========

Slowest operations
------------------
=============================== ======== ========= ======
operation                       time_sec memory_mb counts
=============================== ======== ========= ======
total compute_ruptures          4.89490  7.20703   11    
EventBasedRuptureCalculator.run 1.49722  0.43359   1     
managing sources                1.01588  0.09766   1     
total prefilter                 0.23353  3.40625   46    
reading composite source model  0.09459  0.0       1     
splitting sources               0.07686  0.0       1     
store source_info               0.07294  0.33594   1     
making contexts                 0.03218  0.0       31    
saving ruptures                 0.02807  0.0       11    
unpickling prefilter            0.02037  0.0       46    
reading site collection         0.00961  0.0       1     
unpickling compute_ruptures     0.00458  0.0       11    
reading exposure                0.00187  0.0       1     
setting event years             0.00110  0.0       1     
=============================== ======== ========= ======