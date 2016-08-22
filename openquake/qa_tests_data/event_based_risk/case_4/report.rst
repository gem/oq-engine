Event Based Risk for Turkey reduced
===================================

gem-tstation:/home/michele/ssd/calc_40557.hdf5 updated Mon Aug 22 12:15:53 2016

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
engine_version               '2.1.0-git8cbb23e'                                                                                                                                                                               
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
models/src/as_model.xml 5      Active Shallow Crust 7           30           977   
======================= ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ============
compute_ruptures_max_received_per_task 23,339      
compute_ruptures_num_tasks             8           
compute_ruptures_sent.monitor          48,456      
compute_ruptures_sent.rlzs_by_gsim     282,760     
compute_ruptures_sent.sitecol          10,032      
compute_ruptures_sent.sources          2,957,083   
compute_ruptures_tot_received          101,782     
hazard.input_weight                    43,465      
hazard.n_imts                          2           
hazard.n_levels                        45          
hazard.n_realizations                  3,840       
hazard.n_sites                         14          
hazard.n_sources                       148         
hazard.output_weight                   4,892,160   
hostname                               gem-tstation
require_epsilons                       False       
====================================== ============

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
============ ============ ================= ====== ========= =========== ========== ============= ============= =========
src_group_id source_id    source_class      weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ============ ================= ====== ========= =========== ========== ============= ============= =========
5            AS_TRAS334   AreaSource        244    1         9.341E-04   0.0        2.007         2.007         1        
5            AS_TRAS360   AreaSource        182    1         6.890E-04   0.0        1.393         1.393         1        
5            AS_TRAS346   AreaSource        154    1         8.080E-04   0.0        1.246         1.246         1        
5            AS_TRAS395   AreaSource        122    1         7.141E-04   0.0        1.183         1.183         1        
5            AS_TRAS458   AreaSource        121    1         6.728E-04   0.0        0.988         0.988         1        
5            AS_GEAS479   AreaSource        72     1         0.001       0.0        0.780         0.780         1        
5            AS_TRAS410   AreaSource        81     1         6.909E-04   0.0        0.683         0.683         1        
9            FSBG_TRBG989 AreaSource        33     1         7.551E-04   0.0        0.370         0.370         1        
9            FSBG_TRCS114 SimpleFaultSource 449    1         0.002       0.0        0.083         0.083         1        
9            FSBG_TRCS003 SimpleFaultSource 1,020  934       0.006       0.405      0.061         0.037         934      
9            FSBG_TRCS113 SimpleFaultSource 149    1         0.002       0.0        0.042         0.042         1        
9            FSBG_TRCS439 SimpleFaultSource 233    1         0.002       0.0        0.039         0.039         1        
9            FSBG_TRCS082 SimpleFaultSource 197    1         0.002       0.0        0.029         0.029         1        
9            FSBG_TRCS437 SimpleFaultSource 193    1         0.002       0.0        0.028         0.028         1        
9            FSBG_TRCS141 SimpleFaultSource 116    1         0.002       0.0        0.027         0.027         1        
9            FSBG_TRCS373 SimpleFaultSource 85     1         0.002       0.0        0.022         0.022         1        
9            FSBG_TRCS068 SimpleFaultSource 149    1         0.002       0.0        0.022         0.022         1        
9            FSBG_TRCS322 SimpleFaultSource 194    1         0.002       0.0        0.022         0.022         1        
9            FSBG_BGCS044 SimpleFaultSource 57     1         0.002       0.0        0.019         0.019         1        
9            FSBG_TRCS239 SimpleFaultSource 113    1         0.002       0.0        0.017         0.017         1        
============ ============ ================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================= =========== ========== ============= ============= ========= ======
source_class      filter_time split_time cum_calc_time max_calc_time num_tasks counts
================= =========== ========== ============= ============= ========= ======
AreaSource        0.007       0.0        8.650         8.650         8         8     
SimpleFaultSource 0.043       0.405      0.511         0.486         957       24    
================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         1.146 1.977  0.011 5.426 8        
compute_ruptures.memory_mb        0.059 0.109  0.0   0.238 8        
compute_gmfs_and_curves.time_sec  0.009 0.003  0.006 0.022 30       
compute_gmfs_and_curves.memory_mb 0.007 0.036  0.0   0.199 30       
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         9.166     0.238     8     
reading composite source model 5.969     0.0       1     
managing sources               1.037     0.0       1     
splitting sources              0.405     0.0       1     
total compute_gmfs_and_curves  0.284     0.199     30    
filtering sources              0.207     0.0       148   
compute poes                   0.205     0.0       30    
aggregating hcurves            0.090     0.0       120   
saving gmfs                    0.056     0.0       120   
bulding hazard curves          0.039     0.0       30    
store source_info              0.039     0.0       1     
make contexts                  0.028     0.0       30    
saving ruptures                0.026     0.0       1     
reading exposure               0.008     0.0       1     
filtering ruptures             0.008     0.0       33    
aggregate curves               0.007     0.0       128   
compute and save statistics    0.001     0.0       1     
combine curves_by_rlz          3.519E-04 0.0       1     
reading site collection        7.153E-06 0.0       1     
============================== ========= ========= ======