Event Based Risk for Turkey reduced
===================================

gem-tstation:/home/michele/ssd/calc_993.hdf5 updated Thu Apr 28 15:39:27 2016

num_sites = 14, sitecol = 1.31 KB

Parameters
----------
============================ ===================
calculation_mode             'event_based_risk' 
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           10.0               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         4.0                
complex_fault_mesh_spacing   4.0                
width_of_mfd_bin             0.1                
area_source_discretization   10.0               
random_seed                  323                
master_seed                  42                 
avg_losses                   False              
oqlite_version               '0.13.0-git93d6f64'
============================ ===================

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
AreaSource               0.500  `models/src/as_model.xml <models/src/as_model.xml>`_     simple(0,0,0,0,0,4,0)  4/4             
FaultSourceAndBackground 0.200  `models/src/fsbg_model.xml <models/src/fsbg_model.xml>`_ trivial(0,0,0,0,0,0,0) 0/0             
SeiFaCrust               0.300  `models/src/ss_model.xml <models/src/ss_model.xml>`_     trivial(0,0,0,0,0,0,0) 0/0             
======================== ====== ======================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================== ================= ======================= ============================
trt_id gsims                                                              distances         siteparams              ruptparams                  
====== ================================================================== ================= ======================= ============================
5      AkkarBommer2010 CauzziFaccioli2008 ChiouYoungs2008 ZhaoEtAl2006Asc rhypo rx rjb rrup vs30measured z1pt0 vs30 ztor mag hypo_depth rake dip
====== ================================================================== ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  5,AkkarBommer2010: ['<0,AreaSource,AkkarBommer2010asc_@_@_@_@_@_@,w=0.35>']
  5,CauzziFaccioli2008: ['<1,AreaSource,CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.35>']
  5,ChiouYoungs2008: ['<2,AreaSource,ChiouYoungs2008asc_@_@_@_@_@_@,w=0.2>']
  5,ZhaoEtAl2006Asc: ['<3,AreaSource,ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.1>']>

Number of ruptures per tectonic region type
-------------------------------------------
======================= ====== ==================== =========== ============ ======
source_model            trt_id trt                  num_sources eff_ruptures weight
======================= ====== ==================== =========== ============ ======
models/src/as_model.xml 5      Active Shallow Crust 7           30           977   
======================= ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ==============
event_based_risk_max_received_per_task 4211          
event_based_risk_num_tasks             30            
event_based_risk_sent.assetcol         84360         
event_based_risk_sent.monitor          78390         
event_based_risk_sent.riskinput        107705        
event_based_risk_sent.riskmodel        565140        
event_based_risk_sent.rlzs_assoc       874110        
event_based_risk_tot_received          125992        
hostname                               'gem-tstation'
require_epsilons                       False         
====================================== ==============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 30   
Total number of events   30   
Rupture multiplicity     1.000
======================== =====

Maximum memory allocated for the GMFs
-------------------------------------
The largest GMF block is for trt_model_id=5, contains 2 IMT(s), 4 realization(s)
and has a size of 2.25 KB / num_tasks

Estimated data transfer for the avglosses
-----------------------------------------
14 asset(s) x 4 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 64 tasks = 28 KB

Exposure model
--------------
=========== ==
#assets     14
#taxonomies 9 
=========== ==

======== =======
Taxonomy #Assets
======== =======
RC_HR    1      
RC_LR    3      
RC_MR    1      
SAM_1S   1      
SAM_2S   2      
SAM_3S   1      
SAM_4S   1      
URM_1S   2      
URM_2S   2      
======== =======

Slowest sources
---------------
============ ============ ================= ====== ========= =========== ========== =========
trt_model_id source_id    source_class      weight split_num filter_time split_time calc_time
============ ============ ================= ====== ========= =========== ========== =========
5            AS_TRAS334   AreaSource        244    1         0.002       0.0        4.776    
5            AS_TRAS360   AreaSource        182    1         0.001       0.0        3.847    
5            AS_TRAS346   AreaSource        154    1         0.002       0.0        3.717    
5            AS_TRAS395   AreaSource        122    1         0.002       0.0        3.164    
5            AS_TRAS458   AreaSource        121    1         0.001       0.0        2.465    
5            AS_GEAS479   AreaSource        72     1         0.002       0.0        1.960    
5            AS_TRAS410   AreaSource        81     1         0.002       0.0        1.738    
9            FSBG_TRBG989 AreaSource        33     1         0.002       0.0        0.920    
9            FSBG_TRCS114 SimpleFaultSource 449    1         0.005       0.0        0.261    
9            FSBG_TRCS003 SimpleFaultSource 1,020  934       0.038       1.273      0.223    
9            FSBG_TRCS082 SimpleFaultSource 197    1         0.005       0.0        0.149    
9            FSBG_TRCS439 SimpleFaultSource 233    1         0.020       0.0        0.125    
9            FSBG_TRCS322 SimpleFaultSource 194    1         0.004       0.0        0.117    
9            FSBG_TRCS113 SimpleFaultSource 149    1         0.004       0.0        0.105    
9            FSBG_TRCS437 SimpleFaultSource 193    1         0.004       0.0        0.094    
9            FSBG_TRCS141 SimpleFaultSource 116    1         0.004       0.0        0.093    
9            FSBG_TRCS068 SimpleFaultSource 149    1         0.005       0.0        0.085    
9            FSBG_TRCS239 SimpleFaultSource 113    1         0.005       0.0        0.070    
9            FSBG_TRCS373 SimpleFaultSource 85     1         0.004       0.0        0.063    
9            FSBG_BGCS044 SimpleFaultSource 57     1         0.004       0.0        0.050    
============ ============ ================= ====== ========= =========== ========== =========

Information about the tasks
---------------------------
================================= ===== ===== ===== ======
measurement                       min   max   mean  stddev
compute_ruptures.time_sec         0.040 7.564 1.518 2.844 
compute_ruptures.memory_mb        0.004 0.055 0.021 0.015 
compute_gmfs_and_curves.time_sec  0.006 0.016 0.008 0.002 
compute_gmfs_and_curves.memory_mb 0.0   0.016 0.004 0.005 
event_based_risk.time_sec         0.010 0.052 0.026 0.010 
event_based_risk.memory_mb        0.0   0.023 0.004 0.008 
================================= ===== ===== ===== ======

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         24        0.055     16    
reading composite source model 16        0.0       1     
managing sources               3.744     0.0       1     
splitting sources              1.273     0.0       1     
total event_based_risk         0.793     0.023     30    
filtering sources              0.606     0.0       148   
computing risk                 0.525     0.0       420   
compute poes                   0.249     0.0       60    
total compute_gmfs_and_curves  0.233     0.016     30    
aggregating hcurves            0.177     0.0       120   
building hazard                0.165     0.0       30    
saving gmfs                    0.115     0.0       120   
bulding hazard curves          0.070     0.0       30    
make contexts                  0.064     0.0       60    
store source_info              0.062     0.0       1     
saving event loss tables       0.057     0.0       30    
getting hazard                 0.054     0.0       420   
saving ruptures                0.031     0.0       1     
aggregate losses               0.021     0.0       420   
reading exposure               0.019     0.0       1     
aggregate curves               0.014     0.0       136   
filtering ruptures             0.014     0.0       33    
compute and save statistics    0.005     0.0       1     
reading site collection        1.001E-05 0.0       1     
============================== ========= ========= ======