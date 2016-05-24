Event Based Risk for Turkey reduced
===================================

gem-tstation:/home/michele/ssd/calc_19152.hdf5 updated Tue May 24 14:32:22 2016

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
avg_losses                   True               
oqlite_version               '0.13.0-git1f78261'
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
====== ========================================================================== ================= ======================= ============================
trt_id gsims                                                                      distances         siteparams              ruptparams                  
====== ========================================================================== ================= ======================= ============================
5      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rx rjb rrup vs30measured z1pt0 vs30 ztor mag hypo_depth rake dip
====== ========================================================================== ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  5,AkkarBommer2010(): ['<0,AreaSource,AkkarBommer2010asc_@_@_@_@_@_@,w=0.35>']
  5,CauzziFaccioli2008(): ['<1,AreaSource,CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.35>']
  5,ChiouYoungs2008(): ['<2,AreaSource,ChiouYoungs2008asc_@_@_@_@_@_@,w=0.2>']
  5,ZhaoEtAl2006Asc(): ['<3,AreaSource,ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.1>']>

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
event_based_risk_max_received_per_task 4851          
event_based_risk_num_tasks             30            
event_based_risk_sent.assetcol         84360         
event_based_risk_sent.monitor          79110         
event_based_risk_sent.riskinput        107885        
event_based_risk_sent.riskmodel        541740        
event_based_risk_sent.rlzs_assoc       1262070       
event_based_risk_tot_received          143944        
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
============ ============ ================= ====== ========= =========== ========== =========
trt_model_id source_id    source_class      weight split_num filter_time split_time calc_time
============ ============ ================= ====== ========= =========== ========== =========
5            AS_TRAS334   AreaSource        244    1         9.079E-04   0.0        1.964    
5            AS_TRAS360   AreaSource        182    1         6.878E-04   0.0        1.460    
5            AS_TRAS346   AreaSource        154    1         7.901E-04   0.0        1.426    
5            AS_TRAS395   AreaSource        122    1         6.959E-04   0.0        1.212    
5            AS_TRAS458   AreaSource        121    1         6.559E-04   0.0        0.972    
5            AS_GEAS479   AreaSource        72     1         0.001       0.0        0.738    
5            AS_TRAS410   AreaSource        81     1         6.721E-04   0.0        0.671    
9            FSBG_TRBG989 AreaSource        33     1         6.979E-04   0.0        0.346    
9            FSBG_TRCS114 SimpleFaultSource 449    1         0.002       0.0        0.080    
9            FSBG_TRCS003 SimpleFaultSource 1,020  934       0.003       0.330      0.052    
9            FSBG_TRCS082 SimpleFaultSource 197    1         0.002       0.0        0.038    
9            FSBG_TRCS068 SimpleFaultSource 149    1         0.002       0.0        0.037    
9            FSBG_TRCS113 SimpleFaultSource 149    1         0.002       0.0        0.033    
9            FSBG_TRCS439 SimpleFaultSource 233    1         0.002       0.0        0.031    
9            FSBG_TRCS322 SimpleFaultSource 194    1         0.002       0.0        0.030    
9            FSBG_TRCS437 SimpleFaultSource 193    1         0.002       0.0        0.021    
9            FSBG_TRCS239 SimpleFaultSource 113    1         0.002       0.0        0.018    
9            FSBG_TRCS141 SimpleFaultSource 116    1         0.002       0.0        0.018    
9            FSBG_TRCS373 SimpleFaultSource 85     1         0.002       0.0        0.017    
9            FSBG_BGCS044 SimpleFaultSource 57     1         0.002       0.0        0.017    
============ ============ ================= ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
================= =========== ========== ========= ======
source_class      filter_time split_time calc_time counts
================= =========== ========== ========= ======
AreaSource        0.006       0.0        8.790     8     
SimpleFaultSource 0.040       0.330      0.478     24    
================= =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         0.580 1.113  0.006 2.887 16       
compute_ruptures.memory_mb        0.045 0.082  0.0   0.219 16       
event_based_risk.time_sec         0.014 0.004  0.008 0.019 30       
event_based_risk.memory_mb        0.0   0.0    0.0   0.0   30       
compute_gmfs_and_curves.time_sec  0.010 0.002  0.006 0.014 30       
compute_gmfs_and_curves.memory_mb 0.009 0.042  0.0   0.230 30       
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         9.275     0.219     16    
reading composite source model 6.394     0.0       1     
managing sources               1.261     0.0       1     
compute poes                   0.427     0.0       60    
total event_based_risk         0.410     0.0       30    
splitting sources              0.330     0.0       1     
total compute_gmfs_and_curves  0.298     0.230     30    
building hazard                0.265     0.0       30    
building riskinputs            0.209     0.0       1     
filtering sources              0.184     0.0       148   
aggregating hcurves            0.101     0.0       120   
computing riskmodel            0.091     0.0       420   
saving gmfs                    0.064     0.0       120   
make contexts                  0.062     0.0       60    
bulding hazard curves          0.038     0.0       30    
saving ruptures                0.025     0.0       1     
store source_info              0.024     0.0       1     
saving event loss tables       0.018     0.0       30    
aggregate losses               0.014     0.0       420   
reading exposure               0.010     0.0       1     
aggregate curves               0.009     0.0       136   
filtering ruptures             0.008     0.0       33    
compute and save statistics    0.004     0.0       1     
reading site collection        6.914E-06 0.0       1     
============================== ========= ========= ======