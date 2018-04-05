Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     1,291,888,232      
date           2018-02-02T16:02:49
engine_version 2.9.0-gitd6a3184   
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
AreaSource               0.500  complex(1,2,4,4,0,5,4) 4/4             
FaultSourceAndBackground 0.200  complex(1,2,4,4,0,5,4) 4/4             
SeiFaCrust               0.300  complex(1,2,4,4,0,5,4) 0/0             
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
models/src/as_model.xml   5      Active Shallow Crust 38,280       324,842     
models/src/fsbg_model.xml 9      Active Shallow Crust 4,638        84,623      
========================= ====== ==================== ============ ============

============= =======
#TRT models   2      
#eff_ruptures 42,918 
#tot_ruptures 409,465
#tot_weight   0      
============= =======

Informational data
------------------
========================= ========================================================================================
compute_ruptures.received tot 109.84 KB, max_per_task 7.34 KB                                                     
compute_ruptures.sent     sources 448.16 KB, src_filter 78.04 KB, param 74.76 KB, gsims 21.33 KB, monitor 17.66 KB
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
1        1.000 0.0    1   1   3         3         
2        1.000 NaN    1   1   1         1         
3        1.000 NaN    1   1   1         1         
4        1.000 0.0    1   1   2         2         
5        1.000 0.0    1   1   2         2         
6        1.000 NaN    1   1   1         1         
7        1.000 0.0    1   1   2         2         
8        1.000 NaN    1   1   1         1         
9        1.000 NaN    1   1   1         1         
*ALL*    1.000 0.0    1   1   14        14        
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ================= ============ ========= ========= =========
source_id    source_class      num_ruptures calc_time num_sites num_split
============ ================= ============ ========= ========= =========
FSBG_ITCS073 SimpleFaultSource 51           0.0       1         0        
FSBG_HUAS132 AreaSource        4,746        0.0       1         0        
FSBG_TRCS417 SimpleFaultSource 23           0.0       1         0        
FSBG_TRCS439 SimpleFaultSource 233          0.0       1         0        
FSBG_GBAS018 AreaSource        2,340        0.0       1         0        
FSBG_HRCS020 SimpleFaultSource 142          0.0       1         0        
FSBG_ESCS061 SimpleFaultSource 32           0.0       1         0        
AS_GRAS376   AreaSource        4,131        0.0       1         0        
FSBG_BEAS158 AreaSource        1,692        0.0       1         0        
FSBG_BACS012 SimpleFaultSource 54           0.0       1         0        
AS_ITAS327   AreaSource        6,045        0.0       1         0        
V_CZAS080    AreaSource        84           0.0       1         0        
FSBG_BGBG090 AreaSource        3,186        0.0       1         0        
FSBG_ITCS002 SimpleFaultSource 111          0.0       1         0        
FSBG_RSCS014 SimpleFaultSource 73           0.0       1         0        
FSBG_DZCS003 SimpleFaultSource 386          0.0       1         0        
FSBG_ITAS309 AreaSource        37,224       0.0       1         0        
FSBG_HRCS005 SimpleFaultSource 380          0.0       1         0        
AS_ITAS291   AreaSource        3,213        0.0       1         0        
FSBG_ATBG999 AreaSource        1,458        0.0       1         0        
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
compute_ruptures   0.252 0.214  0.018 0.863 56       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         14        0.266     56    
reading composite source model 12        0.0       1     
managing sources               1.918     0.0       1     
store source_info              0.049     0.0       1     
making contexts                0.041     0.0       32    
saving ruptures                0.036     0.0       56    
reading exposure               0.011     0.0       1     
setting event years            0.002     0.0       1     
reading site collection        6.199E-06 0.0       1     
============================== ========= ========= ======