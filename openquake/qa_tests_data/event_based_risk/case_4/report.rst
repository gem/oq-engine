Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     1,291,888,232      
date           2017-12-06T11:19:35
engine_version 2.9.0-gite55e76e   
============== ===================

num_sites = 14, num_imts = 2

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
random_seed                     323               
master_seed                     42                
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
AreaSource               0.500  complex(0,2,4,4,5,1,4) 4/4             
FaultSourceAndBackground 0.200  complex(0,2,4,4,5,1,4) 4/4             
SeiFaCrust               0.300  complex(0,2,4,4,5,1,4) 0/0             
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
========================= ====== ==================== ============ ============
source_model              grp_id trt                  eff_ruptures tot_ruptures
========================= ====== ==================== ============ ============
models/src/as_model.xml   5      Active Shallow Crust 39,108       324,842     
models/src/fsbg_model.xml 9      Active Shallow Crust 4,638        84,623      
========================= ====== ==================== ============ ============

============= =======
#TRT models   2      
#eff_ruptures 43,746 
#tot_ruptures 409,465
#tot_weight   0      
============= =======

Informational data
------------------
========================= ========================================================================================
compute_ruptures.received tot 93.07 KB, max_per_task 5.5 KB                                                       
compute_ruptures.sent     sources 466.18 KB, src_filter 96.92 KB, param 81.43 KB, gsims 19.36 KB, monitor 19.24 KB
hazard.input_weight       147186.40000000002                                                                      
hazard.n_imts             2                                                                                       
hazard.n_levels           91                                                                                      
hazard.n_realizations     3840                                                                                    
hazard.n_sites            14                                                                                      
hazard.n_sources          148                                                                                     
hazard.output_weight      1274.0                                                                                  
hostname                  tstation.gem.lan                                                                        
require_epsilons          False                                                                                   
========================= ========================================================================================

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
RC_HR    1.000 NaN    1   1   1         1         
RC_LR    1.000 0.0    1   1   3         3         
RC_MR    1.000 NaN    1   1   1         1         
SAM_1S   1.000 NaN    1   1   1         1         
SAM_2S   1.000 0.0    1   1   2         2         
SAM_3S   1.000 NaN    1   1   1         1         
SAM_4S   1.000 NaN    1   1   1         1         
URM_1S   1.000 0.0    1   1   2         2         
URM_2S   1.000 0.0    1   1   2         2         
*ALL*    1.000 0.0    1   1   14        14        
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ================= ============ ========= ========= =========
source_id    source_class      num_ruptures calc_time num_sites num_split
============ ================= ============ ========= ========= =========
AS_TRAS360   AreaSource        7,296        0.0       1         0        
AS_CHAS097   AreaSource        2,475        0.0       1         0        
AS_ATAS164   AreaSource        7,395        0.0       1         0        
FSBG_TRCS223 SimpleFaultSource 7            0.0       1         0        
FSBG_PLAS982 AreaSource        6,768        0.0       1         0        
AS_IEAS021   AreaSource        104,832      0.0       1         0        
AS_ITAS297   AreaSource        1,632        0.0       1         0        
FSBG_ALCS002 SimpleFaultSource 246          0.0       1         0        
AS_TRAS395   AreaSource        4,896        0.0       1         0        
FSBG_BGBG090 AreaSource        3,186        0.0       1         0        
FSBG_GBAS977 AreaSource        104,796      0.0       1         0        
V_CZAS127    AreaSource        336          0.0       1         0        
FSBG_ALCS008 SimpleFaultSource 20           0.0       1         0        
AS_ITAS291   AreaSource        3,213        0.0       1         0        
FSBG_DZBG021 AreaSource        31,347       0.0       1         0        
FSBG_TRCS231 SimpleFaultSource 7            0.0       1         0        
AS_FRAS473   AreaSource        1,974        0.0       1         0        
FSBG_TRCS003 SimpleFaultSource 1,020        0.0       1         0        
AS_ITAS327   AreaSource        6,045        0.0       1         0        
FSBG_GRCS947 SimpleFaultSource 10           0.0       1         0        
============ ================= ============ ========= ========= =========

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
compute_ruptures   0.230 0.240  0.009 0.903 61       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         14        0.211     61    
reading composite source model 12        0.0       1     
managing sources               1.820     0.0       1     
saving ruptures                0.035     0.0       61    
store source_info              0.034     0.0       1     
reading exposure               0.015     0.0       1     
filtering ruptures             0.010     0.0       33    
setting event years            0.001     0.0       1     
reading site collection        7.629E-06 0.0       1     
============================== ========= ========= ======