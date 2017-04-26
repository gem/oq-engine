Event Based Risk for Turkey reduced
===================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7587.hdf5 Wed Apr 26 15:54:41 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 14, sitecol = 1.48 KB

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
======================== ====== ======================================================== ====================== ================
smlt_path                weight source_model_file                                        gsim_logic_tree        num_realizations
======================== ====== ======================================================== ====================== ================
AreaSource               0.500  `models/src/as_model.xml <models/src/as_model.xml>`_     complex(2,5,4,4,1,0,4) 4/4             
FaultSourceAndBackground 0.200  `models/src/fsbg_model.xml <models/src/fsbg_model.xml>`_ complex(2,5,4,4,1,0,4) 0/0             
SeiFaCrust               0.300  `models/src/ss_model.xml <models/src/ss_model.xml>`_     complex(2,5,4,4,1,0,4) 0/0             
======================== ====== ======================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================== ================= ======================= ============================
grp_id gsims                                                                      distances         siteparams              ruptparams                  
====== ========================================================================== ================= ======================= ============================
5      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rx rjb rhypo rrup vs30 vs30measured z1pt0 dip hypo_depth ztor rake mag
====== ========================================================================== ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  5,AkkarBommer2010(): ['<0,AreaSource~AkkarBommer2010asc_@_@_@_@_@_@,w=0.35000000000000003>']
  5,CauzziFaccioli2008(): ['<1,AreaSource~CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.35000000000000003>']
  5,ChiouYoungs2008(): ['<2,AreaSource~ChiouYoungs2008asc_@_@_@_@_@_@,w=0.20000000000000004>']
  5,ZhaoEtAl2006Asc(): ['<3,AreaSource~ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.10000000000000002>']>

Number of ruptures per tectonic region type
-------------------------------------------
======================= ====== ==================== =========== ============ ============
source_model            grp_id trt                  num_sources eff_ruptures tot_ruptures
======================= ====== ==================== =========== ============ ============
models/src/as_model.xml 5      Active Shallow Crust 7           30           39,108      
======================= ====== ==================== =========== ============ ============

Informational data
------------------
============================ =======================================================================================
compute_ruptures.received    tot 147.47 KB, max_per_task 7.48 KB                                                    
compute_ruptures.sent        sources 444.91 KB, monitor 79.79 KB, src_filter 79.44 KB, gsims 15.87 KB, param 3.22 KB
hazard.input_weight          7,937                                                                                  
hazard.n_imts                2 B                                                                                    
hazard.n_levels              91 B                                                                                   
hazard.n_realizations        3.75 KB                                                                                
hazard.n_sites               14 B                                                                                   
hazard.n_sources             36 B                                                                                   
hazard.output_weight         4,892,160                                                                              
hostname                     tstation.gem.lan                                                                       
require_epsilons             0 B                                                                                    
============================ =======================================================================================

Estimated data transfer for the avglosses
-----------------------------------------
14 asset(s) x 4 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 64 tasks = 28 KB

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
====== ============ ================= ============ ========= ========= =========
grp_id source_id    source_class      num_ruptures calc_time num_sites num_split
====== ============ ================= ============ ========= ========= =========
5      AS_TRAS360   AreaSource        7,296        0.0       5         0        
9      FSBG_ARAS462 AreaSource        2,397        0.0       1         0        
9      FSBG_TRCS141 SimpleFaultSource 116          0.0       3         0        
9      FSBG_GRCS912 SimpleFaultSource 32           0.0       3         0        
9      FSBG_TRCS912 SimpleFaultSource 30           0.0       3         0        
5      AS_TRAS395   AreaSource        4,896        0.0       6         0        
9      FSBG_TRCS052 SimpleFaultSource 55           0.0       1         0        
5      AS_TRAS410   AreaSource        3,240        0.0       7         0        
5      AS_TRAS334   AreaSource        9,780        0.0       12        0        
9      FSBG_TRCS082 SimpleFaultSource 197          0.0       1         0        
9      FSBG_TRCS003 SimpleFaultSource 1,020        0.0       5         0        
5      AS_TRAS458   AreaSource        4,845        0.0       4         0        
9      FSBG_TRCS114 SimpleFaultSource 449          0.0       1         0        
5      AS_GEAS479   AreaSource        2,880        0.0       2         0        
9      FSBG_TRCS319 SimpleFaultSource 12           0.0       3         0        
9      FSBG_BGCS044 SimpleFaultSource 57           0.0       1         0        
9      FSBG_TRCS199 SimpleFaultSource 32           0.0       4         0        
9      FSBG_TRCS068 SimpleFaultSource 149          0.0       2         0        
9      FSBG_TRCS417 SimpleFaultSource 23           0.0       3         0        
9      FSBG_TRCS113 SimpleFaultSource 149          0.0       1         0        
====== ============ ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
AreaSource        0.0       9     
SimpleFaultSource 0.0       27    
================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.261 0.279  0.004 1.014 50       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           13        0.531     50    
reading composite source model   5.947     0.0       1     
filtering composite source model 0.150     0.0       1     
saving ruptures                  0.034     0.0       50    
building site collection         0.013     0.0       1     
filtering ruptures               0.009     0.0       32    
reading exposure                 0.003     0.0       1     
setting event years              0.001     0.0       1     
store source_info                6.728E-04 0.0       1     
managing sources                 9.608E-05 0.0       1     
reading site collection          8.345E-06 0.0       1     
================================ ========= ========= ======