Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     3,465,256,954      
date           2018-02-25T06:42:12
engine_version 2.10.0-git1f7c0c0  
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
area_source_discretization      10.0              
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
======================== ====== ====================== ================
smlt_path                weight gsim_logic_tree        num_realizations
======================== ====== ====================== ================
AreaSource               0.500  complex(4,2,4,0,1,4,5) 4/4             
FaultSourceAndBackground 0.200  complex(4,2,4,0,1,4,5) 4/4             
SeiFaCrust               0.300  complex(4,2,4,0,1,4,5) 0/0             
======================== ====== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================== ================= ======================= ============================
grp_id gsims                                                                      distances         siteparams              ruptparams                  
====== ========================================================================== ================= ======================= ============================
5      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
9      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
====== ========================================================================== ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  5,AkkarBommer2010(): [0]
  5,CauzziFaccioli2008(): [1]
  5,ChiouYoungs2008(): [2]
  5,ZhaoEtAl2006Asc(): [3]
  9,AkkarBommer2010(): [4]
  9,CauzziFaccioli2008(): [5]
  9,ChiouYoungs2008(): [6]
  9,ZhaoEtAl2006Asc(): [7]>

Number of ruptures per tectonic region type
-------------------------------------------
===================== ====== ==================== ============ ============
source_model          grp_id trt                  eff_ruptures tot_ruptures
===================== ====== ==================== ============ ============
../src/as_model.xml   5      Active Shallow Crust 38,280       324,842     
../src/fsbg_model.xml 9      Active Shallow Crust 4,341        84,623      
===================== ====== ==================== ============ ============

============= =======
#TRT models   2      
#eff_ruptures 42,621 
#tot_ruptures 409,465
#tot_weight   0      
============= =======

Informational data
------------------
========================= ===================================================================================
compute_ruptures.received tot 52.87 KB, max_per_task 32.34 KB                                                
compute_ruptures.sent     sources 401.77 KB, src_filter 6.97 KB, param 6.67 KB, gsims 1.9 KB, monitor 1.61 KB
hazard.input_weight       147186.40000000002                                                                 
hazard.n_imts             2                                                                                  
hazard.n_levels           91                                                                                 
hazard.n_realizations     3840                                                                               
hazard.n_sites            14                                                                                 
hazard.n_sources          148                                                                                
hazard.output_weight      1274.0                                                                             
hostname                  tstation.gem.lan                                                                   
require_epsilons          False                                                                              
========================= ===================================================================================

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

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
RC_LR    1.000 0.0    1   1   3         3         
RC_MR    1.000 NaN    1   1   1         1         
RC_HR    1.000 NaN    1   1   1         1         
URM_1S   1.000 0.0    1   1   2         2         
URM_2S   1.000 0.0    1   1   2         2         
SAM_1S   1.000 NaN    1   1   1         1         
SAM_2S   1.000 0.0    1   1   2         2         
SAM_3S   1.000 NaN    1   1   1         1         
SAM_4S   1.000 NaN    1   1   1         1         
*ALL*    1.000 0.0    1   1   14        14        
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============== ================== ============ ========= ========= =========
source_id      source_class       num_ruptures calc_time num_sites num_split
============== ================== ============ ========= ========= =========
FSBG_NOAS056   AreaSource         15,156       0.0       1         0        
AS_GEAS479     AreaSource         2,880        0.0       1         0        
FSBG_TRCS038   SimpleFaultSource  21           0.0       1         0        
IF_HELL_GRID01 ComplexFaultSource 3,858        0.0       1         0        
FSBG_MDAS229   AreaSource         23,256       0.0       1         0        
FSBG_TRCS090   SimpleFaultSource  245          0.0       1         0        
FSBG_MKCS011   SimpleFaultSource  34           0.0       1         0        
AS_ATAS164     AreaSource         7,395        0.0       1         0        
FSBG_DEAS155   AreaSource         5,472        0.0       1         0        
FSBG_TRCS319   SimpleFaultSource  12           0.0       1         0        
FSBG_TRCS374   SimpleFaultSource  64           0.0       1         0        
FSBG_MECS005   SimpleFaultSource  26           0.0       1         0        
FSBG_TRCS156   SimpleFaultSource  39           0.0       1         0        
AS_GRAS376     AreaSource         4,131        0.0       1         0        
AS_TRAS395     AreaSource         4,896        0.0       1         0        
FSBG_TRCS322   SimpleFaultSource  194          0.0       1         0        
FSBG_ESAS971   AreaSource         15,288       0.0       1         0        
FSBG_HRCS020   SimpleFaultSource  142          0.0       1         0        
FSBG_GRCS605   SimpleFaultSource  362          0.0       1         0        
FSBG_TRCS099   SimpleFaultSource  47           0.0       1         0        
============== ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.0       71    
ComplexFaultSource 0.0       1     
PointSource        0.0       1     
SimpleFaultSource  0.0       75    
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   2.268 2.586  0.164 5.818 5        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               14        0.0       1     
reading composite source model 12        0.0       1     
total compute_ruptures         11        0.500     5     
store source_info              0.057     0.0       1     
making contexts                0.020     0.0       32    
saving ruptures                0.012     0.0       5     
reading exposure               0.003     0.0       1     
setting event years            0.002     0.0       1     
reading site collection        6.914E-06 0.0       1     
============================== ========= ========= ======