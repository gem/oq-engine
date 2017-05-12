Event Based Risk for Turkey reduced
===================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_20414.hdf5 Fri May 12 06:36:46 2017
engine_version                                   2.4.0-giteadb85d        
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
AreaSource               0.500  `models/src/as_model.xml <models/src/as_model.xml>`_     complex(5,1,4,4,0,2,4) 4/4             
FaultSourceAndBackground 0.200  `models/src/fsbg_model.xml <models/src/fsbg_model.xml>`_ complex(5,1,4,4,0,2,4) 0/0             
SeiFaCrust               0.300  `models/src/ss_model.xml <models/src/ss_model.xml>`_     complex(5,1,4,4,0,2,4) 0/0             
======================== ====== ======================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================== ================= ======================= ============================
grp_id gsims                                                                      distances         siteparams              ruptparams                  
====== ========================================================================== ================= ======================= ============================
5      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rrup rx rjb vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
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
============================ =================================================================================
compute_ruptures.received    tot 46.49 KB, max_per_task 26.92 KB                                              
compute_ruptures.sent        sources 4.9 MB, monitor 17.56 KB, src_filter 17.48 KB, gsims 2.88 KB, param 726 B
hazard.input_weight          147,186                                                                          
hazard.n_imts                2 B                                                                              
hazard.n_levels              91 B                                                                             
hazard.n_realizations        3.75 KB                                                                          
hazard.n_sites               14 B                                                                             
hazard.n_sources             148 B                                                                            
hazard.output_weight         4,892,160                                                                        
hostname                     tstation.gem.lan                                                                 
require_epsilons             0 B                                                                              
============================ =================================================================================

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
9      FSBG_GRCS750 SimpleFaultSource 14           0.0       0         0        
9      FSBG_ATCS002 SimpleFaultSource 16           0.0       0         0        
9      FSBG_GRCS605 SimpleFaultSource 362          0.0       0         0        
9      FSBG_ALCS021 SimpleFaultSource 8            0.0       0         0        
5      AS_ATAS164   AreaSource        7,395        0.0       0         0        
9      FSBG_TRCS437 SimpleFaultSource 193          0.0       0         0        
5      AS_ISAS072   AreaSource        1,632        0.0       0         0        
5      AS_ITAS285   AreaSource        1,755        0.0       0         0        
5      AS_ITAS324   AreaSource        585          0.0       0         0        
8      FSBG_PTCS001 SimpleFaultSource 78           0.0       0         0        
5      AS_CHAS092   AreaSource        3,690        0.0       0         0        
8      FSBG_DZBG021 AreaSource        31,347       0.0       0         0        
9      FSBG_ATCS001 SimpleFaultSource 204          0.0       0         0        
9      FSBG_TRCS239 SimpleFaultSource 113          0.0       0         0        
9      FSBG_ESAS971 AreaSource        15,288       0.0       0         0        
4      AS_IEAS021   AreaSource        104,832      0.0       0         0        
5      AS_BAAS192   AreaSource        13,005       0.0       0         0        
5      AS_TRAS334   AreaSource        9,780        0.0       0         0        
9      FSBG_GRCS583 SimpleFaultSource 16           0.0       0         0        
9      FSBG_HRCS005 SimpleFaultSource 380          0.0       0         0        
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
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.734 2.135  0.001 7.126 11       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           8.078     1.957     11    
reading composite source model   5.852     0.0       1     
managing sources                 0.032     0.0       1     
reading exposure                 0.017     0.0       1     
filtering ruptures               0.007     0.0       33    
saving ruptures                  0.007     0.0       11    
store source_info                0.003     0.0       1     
setting event years              0.002     0.0       1     
filtering composite source model 2.861E-05 0.0       1     
reading site collection          8.583E-06 0.0       1     
================================ ========= ========= ======