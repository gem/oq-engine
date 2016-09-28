Event Based Risk for Turkey reduced
===================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_54397.hdf5 Tue Sep 27 14:06:15 2016
engine_version                                 2.1.0-git1ca7123        
hazardlib_version                              0.21.0-git9261682       
============================================== ========================

num_sites = 14, sitecol = 1.31 KB

Parameters
----------
============================ =================================================================================================================================================================================================
calculation_mode             'event_based_risk'                                                                                                                                                                               
number_of_logic_tree_samples 0                                                                                                                                                                                                
maximum_distance             {u'Volcanic': 200.0, u'Shield': 200.0, u'Active Shallow Crust': 200.0, u'Subduction Interface': 200.0, u'Stable Shallow Crust': 200.0, u'Subduction Deep': 200.0, u'Subduction IntraSlab': 200.0}
investigation_time           10.0                                                                                                                                                                                             
ses_per_logic_tree_path      1                                                                                                                                                                                                
truncation_level             3.0                                                                                                                                                                                              
rupture_mesh_spacing         4.0                                                                                                                                                                                              
complex_fault_mesh_spacing   4.0                                                                                                                                                                                              
width_of_mfd_bin             0.1                                                                                                                                                                                              
area_source_discretization   10.0                                                                                                                                                                                             
random_seed                  323                                                                                                                                                                                              
master_seed                  42                                                                                                                                                                                               
avg_losses                   True                                                                                                                                                                                             
============================ =================================================================================================================================================================================================

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
AreaSource               0.500  `models/src/as_model.xml <models/src/as_model.xml>`_     complex(1,2,5,0,4,4,4) 4/4             
FaultSourceAndBackground 0.200  `models/src/fsbg_model.xml <models/src/fsbg_model.xml>`_ complex(1,2,5,0,4,4,4) 0/0             
SeiFaCrust               0.300  `models/src/ss_model.xml <models/src/ss_model.xml>`_     complex(1,2,5,0,4,4,4) 0/0             
======================== ====== ======================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================== ================= ======================= ============================
grp_id gsims                                                                      distances         siteparams              ruptparams                  
====== ========================================================================== ================= ======================= ============================
5      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rx rjb rrup vs30measured z1pt0 vs30 ztor mag hypo_depth rake dip
====== ========================================================================== ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  5,AkkarBommer2010(): ['<0,AreaSource~AkkarBommer2010asc_@_@_@_@_@_@,w=0.35>']
  5,CauzziFaccioli2008(): ['<1,AreaSource~CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.35>']
  5,ChiouYoungs2008(): ['<2,AreaSource~ChiouYoungs2008asc_@_@_@_@_@_@,w=0.2>']
  5,ZhaoEtAl2006Asc(): ['<3,AreaSource~ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.1>']>

Number of ruptures per tectonic region type
-------------------------------------------
======================= ====== ==================== =========== ============ ======
source_model            grp_id trt                  num_sources eff_ruptures weight
======================= ====== ==================== =========== ============ ======
models/src/as_model.xml 5      Active Shallow Crust 30          30           3,626 
======================= ====== ==================== =========== ============ ======

Informational data
------------------
============================================= ============
compute_gmfs_and_curves_max_received_per_task 22,437      
compute_gmfs_and_curves_num_tasks             30          
compute_gmfs_and_curves_sent.eb_ruptures      58,951      
compute_gmfs_and_curves_sent.imts             780         
compute_gmfs_and_curves_sent.min_iml          4,110       
compute_gmfs_and_curves_sent.monitor          174,900     
compute_gmfs_and_curves_sent.rlzs_by_gsim     55,650      
compute_gmfs_and_curves_sent.sitecol          40,110      
compute_gmfs_and_curves_tot_received          504,526     
compute_ruptures_max_received_per_task        18,011      
compute_ruptures_num_tasks                    37          
compute_ruptures_sent.gsims                   11,608      
compute_ruptures_sent.monitor                 72,810      
compute_ruptures_sent.sitecol                 46,632      
compute_ruptures_sent.sources                 4,345,484   
compute_ruptures_tot_received                 143,866     
hazard.input_weight                           43,465      
hazard.n_imts                                 2           
hazard.n_levels                               91          
hazard.n_realizations                         3,840       
hazard.n_sites                                14          
hazard.n_sources                              148         
hazard.output_weight                          4,892,160   
hostname                                      gem-tstation
require_epsilons                              False       
============================================= ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 30   
Total number of events   30   
Rupture multiplicity     1.000
======================== =====

Maximum memory allocated for the GMFs
-------------------------------------
The largest GMF block is for src_group_id=5, contains 2 IMT(s), 4 realization(s)
and has a size of 2.25 KB / num_tasks

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
====== ============ ================= ====== ========= =========
grp_id source_id    source_class      weight calc_time num_sites
====== ============ ================= ====== ========= =========
5      AS_TRAS395   AreaSource        122    0.0       0        
9      FSBG_ATCS001 SimpleFaultSource 204    0.0       0        
9      FSBG_TRCS068 SimpleFaultSource 149    0.0       0        
9      FSBG_TRCS052 SimpleFaultSource 55     0.0       0        
9      FSBG_TRCS437 SimpleFaultSource 193    0.0       0        
5      AS_GRAS369   AreaSource        198    0.0       0        
9      FSBG_BGCS044 SimpleFaultSource 57     0.0       0        
9      FSBG_ALCS021 SimpleFaultSource 8.000  0.0       0        
9      FSBG_HRCS039 SimpleFaultSource 27     0.0       0        
4      AS_BEAS177   AreaSource        257    0.0       0        
5      AS_CHAS092   AreaSource        92     0.0       0        
8      FSBG_DEAS156 AreaSource        22     0.0       0        
9      FSBG_BGBG090 AreaSource        79     0.0       0        
4      AS_NOAS055   AreaSource        458    0.0       0        
9      FSBG_ESBG038 AreaSource        111    0.0       0        
9      FSBG_HRCS020 SimpleFaultSource 142    0.0       0        
5      AS_HRAS083   AreaSource        239    0.0       0        
9      FSBG_GRCS155 SimpleFaultSource 30     0.0       0        
9      FSBG_ITCS073 SimpleFaultSource 51     0.0       0        
8      FSBG_DZCS012 SimpleFaultSource 198    0.0       0        
====== ============ ================= ====== ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
AreaSource        0.0       59    
PointSource       0.0       1     
SimpleFaultSource 0.0       75    
================= ========= ======

Information about the tasks
---------------------------
======================= ===== ====== ===== ===== =========
operation-duration      mean  stddev min   max   num_tasks
compute_ruptures        0.250 0.879  0.001 4.651 37       
compute_gmfs_and_curves 0.017 0.004  0.011 0.025 30       
======================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         9.243     4.055     37    
reading composite source model 5.976     0.0       1     
total compute_gmfs_and_curves  0.515     0.316     30    
managing sources               0.509     0.0       1     
filter/split heavy sources     0.443     0.0       7     
compute poes                   0.362     0.0       30    
building hazard curves         0.083     0.0       30    
saving ruptures                0.056     0.0       37    
saving gmfs                    0.041     0.0       30    
make contexts                  0.033     0.0       30    
reading exposure               0.010     0.0       1     
filtering ruptures             0.007     0.0       33    
aggregating hcurves            0.006     0.0       30    
store source_info              0.002     0.0       1     
reading site collection        8.106E-06 0.0       1     
============================== ========= ========= ======