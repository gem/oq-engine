Event Based Risk for Turkey reduced
===================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_81049.hdf5 Thu Jan 26 14:28:38 2017
engine_version                                 2.3.0-gite807292        
hazardlib_version                              0.23.0-gite1ea7ea       
============================================== ========================

num_sites = 14, sitecol = 1.33 KB

Parameters
----------
=============================== ==========================================================================================================================================================================================
calculation_mode                'event_based_risk'                                                                                                                                                                        
number_of_logic_tree_samples    0                                                                                                                                                                                         
maximum_distance                {'Stable Shallow Crust': 200.0, 'Subduction Deep': 200.0, 'Subduction IntraSlab': 200.0, 'Active Shallow Crust': 200.0, 'Volcanic': 200.0, 'Shield': 200.0, 'Subduction Interface': 200.0}
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
=============================== ==========================================================================================================================================================================================

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
AreaSource               0.500  `models/src/as_model.xml <models/src/as_model.xml>`_     complex(4,5,1,4,2,0,4) 4/4             
FaultSourceAndBackground 0.200  `models/src/fsbg_model.xml <models/src/fsbg_model.xml>`_ complex(4,5,1,4,2,0,4) 0/0             
SeiFaCrust               0.300  `models/src/ss_model.xml <models/src/ss_model.xml>`_     complex(4,5,1,4,2,0,4) 0/0             
======================== ====== ======================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================== ================= ======================= ============================
grp_id gsims                                                                      distances         siteparams              ruptparams                  
====== ========================================================================== ================= ======================= ============================
5      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rrup rjb rhypo rx vs30measured vs30 z1pt0 rake dip hypo_depth ztor mag
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
========================================= ============
compute_ruptures_max_received_per_task    9,274       
compute_ruptures_num_tasks                50          
compute_ruptures_sent.gsims               16,250      
compute_ruptures_sent.monitor             96,850      
compute_ruptures_sent.sources             455,592     
compute_ruptures_sent.src_filter          79,950      
compute_ruptures_tot_received             194,469     
hazard.input_weight                       7,937       
hazard.n_imts                             2           
hazard.n_levels                           91          
hazard.n_realizations                     3,840       
hazard.n_sites                            14          
hazard.n_sources                          36          
hazard.output_weight                      4,892,160   
hostname                                  gem-tstation
require_epsilons                          False       
========================================= ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 30   
Total number of events   30   
Rupture multiplicity     1.000
======================== =====

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
9      FSBG_TRCS038 SimpleFaultSource 21           0.0       4         0        
5      AS_TRAS395   AreaSource        4,896        0.0       6         0        
9      FSBG_TRCS090 SimpleFaultSource 245          0.0       1         0        
5      AS_TRAS410   AreaSource        3,240        0.0       7         0        
9      FSBG_TRCS114 SimpleFaultSource 449          0.0       1         0        
9      FSBG_TRCS912 SimpleFaultSource 30           0.0       3         0        
9      FSBG_TRCS156 SimpleFaultSource 39           0.0       2         0        
5      AS_TRAS334   AreaSource        9,780        0.0       12        0        
9      FSBG_BGCS044 SimpleFaultSource 57           0.0       1         0        
5      AS_TRAS458   AreaSource        4,845        0.0       4         0        
9      FSBG_TRCS082 SimpleFaultSource 197          0.0       1         0        
9      FSBG_TRCS052 SimpleFaultSource 55           0.0       1         0        
9      FSBG_TRCS373 SimpleFaultSource 85           0.0       1         0        
9      FSBG_TRCS231 SimpleFaultSource 7            0.0       5         0        
5      AS_GEAS479   AreaSource        2,880        0.0       2         0        
9      FSBG_TRCS199 SimpleFaultSource 32           0.0       4         0        
9      FSBG_TRCS068 SimpleFaultSource 149          0.0       2         0        
9      FSBG_GRCS912 SimpleFaultSource 32           0.0       3         0        
9      FSBG_TRCS437 SimpleFaultSource 193          0.0       3         0        
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
compute_ruptures   0.269 0.288  0.004 1.083 50       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           13        0.258     50    
reading composite source model   6.237     0.0       1     
managing sources                 1.431     0.0       1     
split/filter heavy sources       1.419     0.0       2     
filtering composite source model 0.155     0.0       1     
saving ruptures                  0.025     0.0       50    
reading exposure                 0.014     0.0       1     
filtering ruptures               0.011     0.0       32    
setting event years              0.002     0.0       1     
store source_info                0.001     0.0       1     
reading site collection          1.001E-05 0.0       1     
================================ ========= ========= ======