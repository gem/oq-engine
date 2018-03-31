Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     3,465,256,954      
date           2018-03-26T15:55:10
engine_version 2.10.0-git543cfb0  
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
AreaSource               0.500  complex(2,1,4,0,5,4,4) 4/4             
FaultSourceAndBackground 0.200  complex(2,1,4,0,5,4,4) 4/4             
SeiFaCrust               0.300  complex(2,1,4,0,5,4,4) 0/0             
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
============ ================= ============ ========= ========== ========= =========
source_id    source_class      num_ruptures calc_time split_time num_sites num_split
============ ================= ============ ========= ========== ========= =========
FSBG_TRCS284 SimpleFaultSource 23           0.0       6.747E-05  0         0        
FSBG_GRCS583 SimpleFaultSource 16           0.0       6.390E-05  0         0        
FSBG_TRCS374 SimpleFaultSource 64           0.0       9.012E-05  0         0        
FSBG_DEAS155 AreaSource        5,472        0.0       0.045      0         0        
FSBG_GRCS250 SimpleFaultSource 79           0.0       8.297E-05  0         0        
AS_GRAS369   AreaSource        7,956        0.0       0.026      0         0        
AS_ITAS297   AreaSource        1,632        0.0       0.006      0         0        
FSBG_TRCS437 SimpleFaultSource 193          0.0       8.416E-05  0         0        
FSBG_DEAS972 AreaSource        3,144        0.0       0.023      0         0        
AS_CHAS092   AreaSource        3,690        0.0       0.016      0         0        
FSBG_TRCS141 SimpleFaultSource 116          0.0       1.028E-04  0         0        
FSBG_TRCS090 SimpleFaultSource 245          0.0       1.640E-04  0         0        
FSBG_TRCS223 SimpleFaultSource 7            0.0       5.054E-05  0         0        
FSBG_GRCS100 SimpleFaultSource 120          0.0       1.080E-04  0         0        
AS_ITAS327   AreaSource        6,045        0.0       0.038      0         0        
FSBG_ARAS462 AreaSource        2,397        0.0       0.019      0         0        
FSBG_NOAS056 AreaSource        15,156       0.0       0.060      0         0        
FSBG_RSCS014 SimpleFaultSource 73           0.0       8.273E-05  0         0        
FSBG_TRCS417 SimpleFaultSource 23           0.0       6.819E-05  0         0        
AS_YUAS221   AreaSource        5,445        0.0       0.025      0         0        
============ ================= ============ ========= ========== ========= =========

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
compute_ruptures   0.350 0.284  0.009 0.740 72       
================== ===== ====== ===== ===== =========

Informational data
------------------
================ ==================================================================================== ========
task             sent                                                                                 received
compute_ruptures sources=524.58 KB src_filter=100.34 KB param=96.12 KB gsims=27.42 KB monitor=23.2 KB 80.68 KB
================ ==================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         25        2.645     72    
reading composite source model 12        0.0       1     
splitting sources              6.132     30        1     
managing sources               4.257     0.0       1     
saving ruptures                0.094     0.0       72    
making contexts                0.046     0.0       32    
store source_info              0.034     0.0       1     
reading exposure               0.027     0.0       1     
unpickling compute_ruptures    0.006     0.0       72    
setting event years            0.001     0.0       1     
reading site collection        4.673E-05 0.0       1     
============================== ========= ========= ======