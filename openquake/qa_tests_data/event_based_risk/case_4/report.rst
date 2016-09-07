Event Based Risk for Turkey reduced
===================================

============================================== ================================
gem-tstation:/home/michele/ssd/calc_48271.hdf5 updated Wed Sep  7 15:56:07 2016
engine_version                                 2.1.0-git3a14ca6                
hazardlib_version                              0.21.0-git89bccaf               
============================================== ================================

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
models/src/as_model.xml 5      Active Shallow Crust 7           30           977   
======================= ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ============
compute_ruptures_max_received_per_task 18,956      
compute_ruptures_num_tasks             8           
compute_ruptures_sent.gsims            2,480       
compute_ruptures_sent.monitor          14,834      
compute_ruptures_sent.sitecol          10,266      
compute_ruptures_sent.sources          2,957,083   
compute_ruptures_tot_received          65,410      
hazard.input_weight                    43,465      
hazard.n_imts                          2           
hazard.n_levels                        91          
hazard.n_realizations                  3,840       
hazard.n_sites                         14          
hazard.n_sources                       148         
hazard.output_weight                   9,784,320   
hostname                               gem-tstation
require_epsilons                       False       
====================================== ============

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
5            AS_TRAS334   AreaSource        244    0         9.432E-04   0.0        1.998         1.998         1        
5            AS_TRAS360   AreaSource        182    0         6.950E-04   0.0        1.477         1.477         1        
5            AS_TRAS346   AreaSource        154    0         8.149E-04   0.0        1.243         1.243         1        
5            AS_TRAS395   AreaSource        122    0         7.191E-04   0.0        1.214         1.214         1        
5            AS_TRAS458   AreaSource        121    0         6.809E-04   0.0        1.005         1.005         1        
5            AS_GEAS479   AreaSource        72     0         0.001       0.0        0.781         0.781         1        
5            AS_TRAS410   AreaSource        81     0         7.122E-04   0.0        0.651         0.651         1        
9            FSBG_TRBG989 AreaSource        33     0         7.720E-04   0.0        0.365         0.365         1        
9            FSBG_TRCS114 SimpleFaultSource 449    0         0.002       0.0        0.078         0.078         1        
9            FSBG_TRCS003 SimpleFaultSource 1,020  934       0.0         0.377      0.060         0.036         934      
9            FSBG_TRCS113 SimpleFaultSource 149    0         0.002       0.0        0.038         0.038         1        
9            FSBG_TRCS141 SimpleFaultSource 116    0         0.002       0.0        0.035         0.035         1        
9            FSBG_TRCS439 SimpleFaultSource 233    0         0.002       0.0        0.028         0.028         1        
9            FSBG_TRCS082 SimpleFaultSource 197    0         0.002       0.0        0.028         0.028         1        
9            FSBG_TRCS322 SimpleFaultSource 194    0         0.002       0.0        0.024         0.024         1        
9            FSBG_TRCS373 SimpleFaultSource 85     0         0.002       0.0        0.024         0.024         1        
9            FSBG_TRCS437 SimpleFaultSource 193    0         0.002       0.0        0.023         0.023         1        
9            FSBG_TRCS068 SimpleFaultSource 149    0         0.002       0.0        0.022         0.022         1        
9            FSBG_BGCS044 SimpleFaultSource 57     0         0.002       0.0        0.019         0.019         1        
9            FSBG_TRCS239 SimpleFaultSource 113    0         0.002       0.0        0.019         0.019         1        
============ ============ ================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================= =========== ========== ============= ============= ========= ======
source_class      filter_time split_time cum_calc_time max_calc_time num_tasks counts
================= =========== ========== ============= ============= ========= ======
AreaSource        0.007       0.0        8.734         8.734         8         8     
SimpleFaultSource 0.038       0.377      0.508         0.484         957       24    
================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
======================= ===== ====== ===== ===== =========
operation-duration      mean  stddev min   max   num_tasks
compute_gmfs_and_curves 0.012 0.003  0.007 0.024 30       
compute_ruptures        1.162 1.999  0.027 5.500 8        
======================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         9.295     2.238     8     
reading composite source model 6.246     0.0       1     
managing sources               0.928     0.0       1     
total compute_gmfs_and_curves  0.351     0.020     30    
compute poes                   0.201     0.0       30    
filtering sources              0.175     0.0       134   
building hazard curves         0.086     0.0       30    
saving gmfs                    0.042     0.0       30    
store source_info              0.033     0.0       1     
make contexts                  0.030     0.0       30    
reading exposure               0.010     0.0       1     
saving ruptures                0.009     0.0       8     
filtering ruptures             0.007     0.0       33    
aggregating hcurves            0.006     0.0       30    
reading site collection        6.914E-06 0.0       1     
============================== ========= ========= ======