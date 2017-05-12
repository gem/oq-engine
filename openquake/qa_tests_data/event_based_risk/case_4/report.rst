Event Based Risk for Turkey reduced
===================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_21310.hdf5 Fri May 12 10:45:36 2017
engine_version                                   2.4.0-git59713b5        
hazardlib_version                                0.24.0-git0596dd3       
================================================ ========================

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
AreaSource               0.500  `models/src/as_model.xml <models/src/as_model.xml>`_     complex(2,5,0,4,1,4,4) 4/4             
FaultSourceAndBackground 0.200  `models/src/fsbg_model.xml <models/src/fsbg_model.xml>`_ complex(2,5,0,4,1,4,4) 0/0             
SeiFaCrust               0.300  `models/src/ss_model.xml <models/src/ss_model.xml>`_     complex(2,5,0,4,1,4,4) 0/0             
======================== ====== ======================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================== ================= ======================= ============================
grp_id gsims                                                                      distances         siteparams              ruptparams                  
====== ========================================================================== ================= ======================= ============================
5      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
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
models/src/as_model.xml 5      Active Shallow Crust 32          30           324,842     
======================= ====== ==================== =========== ============ ============

Informational data
------------------
============================ =====================================================================================
compute_ruptures.received    tot 109.98 KB, max_per_task 17.19 KB                                                 
compute_ruptures.sent        sources 4.94 MB, monitor 68.66 KB, src_filter 68.32 KB, gsims 14.23 KB, param 2.77 KB
hazard.input_weight          147,186                                                                              
hazard.n_imts                2 B                                                                                  
hazard.n_levels              91 B                                                                                 
hazard.n_realizations        3.75 KB                                                                              
hazard.n_sites               14 B                                                                                 
hazard.n_sources             148 B                                                                                
hazard.output_weight         1,274                                                                                
hostname                     tstation.gem.lan                                                                     
require_epsilons             0 B                                                                                  
============================ =====================================================================================

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
7      V_CZAS127    AreaSource        336          0.0       0         0        
9      FSBG_TRCS374 SimpleFaultSource 64           0.0       0         0        
9      FSBG_TRCS322 SimpleFaultSource 194          0.0       0         0        
10     100041       PointSource       27           0.0       0         0        
9      FSBG_TRCS373 SimpleFaultSource 85           0.0       0         0        
9      FSBG_MKCS011 SimpleFaultSource 34           0.0       0         0        
5      AS_CHAS092   AreaSource        3,690        0.0       0         0        
5      AS_TRAS334   AreaSource        9,780        0.0       0         0        
9      FSBG_TNCS001 SimpleFaultSource 680          0.0       0         0        
9      FSBG_BACS009 SimpleFaultSource 58           0.0       0         0        
9      FSBG_HRCS005 SimpleFaultSource 380          0.0       0         0        
5      AS_TRAS395   AreaSource        4,896        0.0       0         0        
9      FSBG_TRCS114 SimpleFaultSource 449          0.0       0         0        
9      FSBG_GRCS240 SimpleFaultSource 10           0.0       0         0        
9      FSBG_HRCS039 SimpleFaultSource 27           0.0       0         0        
5      AS_FRAS473   AreaSource        1,974        0.0       0         0        
9      FSBG_BGCS022 SimpleFaultSource 38           0.0       0         0        
9      FSBG_ALCS014 SimpleFaultSource 39           0.0       0         0        
5      AS_ITAS285   AreaSource        1,755        0.0       0         0        
5      AS_ISAS072   AreaSource        1,632        0.0       0         0        
====== ============ ================= ============ ========= ========= =========

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

Information about the tasks
---------------------------
================== ===== ====== ========= ===== =========
operation-duration mean  stddev min       max   num_tasks
compute_ruptures   0.210 0.768  5.300E-04 3.966 43       
================== ===== ====== ========= ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           9.022     0.508     43    
reading composite source model   6.303     0.0       1     
managing sources                 0.068     0.0       1     
reading exposure                 0.017     0.0       1     
saving ruptures                  0.014     0.0       43    
filtering ruptures               0.007     0.0       33    
store source_info                0.003     0.0       1     
setting event years              0.002     0.0       1     
filtering composite source model 1.421E-04 0.0       1     
reading site collection          7.868E-06 0.0       1     
================================ ========= ========= ======