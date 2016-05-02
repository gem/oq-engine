Virtual Island - City C, 2 SES, grid=0.1
========================================

gem-tstation:/home/michele/ssd/calc_2007.hdf5 updated Fri Apr 29 11:26:55 2016

num_sites = 1792, sitecol = 44.71 KB

Parameters
----------
============================ ===================
calculation_mode             'event_based_risk' 
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           50.0               
ses_per_logic_tree_path      2                  
truncation_level             4.0                
rupture_mesh_spacing         10.0               
complex_fault_mesh_spacing   10.0               
width_of_mfd_bin             0.2                
area_source_discretization   None               
random_seed                  1024               
master_seed                  100                
avg_losses                   False              
oqlite_version               '0.13.0-git920d730'
============================ ===================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1,0)    1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =============== ========= ========== ==========
trt_id gsims           distances siteparams ruptparams
====== =============== ========= ========== ==========
0      AkkarBommer2010 rjb       vs30       rake mag  
====== =============== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,AkkarBommer2010: ['<0,b1,b1_@,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           44           2,558 
================ ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ==============
event_based_risk_max_received_per_task 1973          
event_based_risk_num_tasks             44            
event_based_risk_sent.assetcol         978428        
event_based_risk_sent.monitor          26532         
event_based_risk_sent.riskinput        2203406       
event_based_risk_sent.riskmodel        869528        
event_based_risk_sent.rlzs_assoc       133408        
event_based_risk_tot_received          86460         
hostname                               'gem-tstation'
require_epsilons                       True          
====================================== ==============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 44   
Total number of events   45   
Rupture multiplicity     1.023
======================== =====

Maximum memory allocated for the GMFs
-------------------------------------
The largest GMF block is for trt_model_id=0, contains 1 IMT(s), 1 realization(s)
and has a size of 49.39 KB / num_tasks

Estimated data transfer for the avglosses
-----------------------------------------
548 asset(s) x 1 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 40 tasks = 171.25 KB

Exposure model
--------------
=========== ===
#assets     548
#taxonomies 11 
=========== ===

========== =======
Taxonomy   #Assets
========== =======
A-SPSB-1   10     
MC-RCSB-1  27     
MC-RLSB-2  49     
MR-RCSB-2  249    
MR-SLSB-1  5      
MS-FLSB-2  15     
MS-SLSB-1  17     
PCR-RCSM-5 2      
PCR-SLSB-1 3      
W-FLFB-2   66     
W-SLFB-1   105    
========== =======

Slowest sources
---------------
============ ========= ================== ====== ========= =========== ========== =========
trt_model_id source_id source_class       weight split_num filter_time split_time calc_time
============ ========= ================== ====== ========= =========== ========== =========
0            F         ComplexFaultSource 2,558  1,119     0.002       2.572      3.251    
============ ========= ================== ====== ========= =========== ========== =========

Information about the tasks
---------------------------
========================== ===== ===== ===== ======
measurement                min   max   mean  stddev
compute_ruptures.time_sec  0.002 0.561 0.078 0.175 
compute_ruptures.memory_mb 0.0   3.598 1.078 1.292 
event_based_risk.time_sec  0.044 0.116 0.074 0.017 
event_based_risk.memory_mb 0.105 1.680 0.989 0.525 
========================== ===== ===== ===== ======

Slowest operations
------------------
============================== ======== ========= ======
operation                      time_sec memory_mb counts
============================== ======== ========= ======
total compute_ruptures         3.291    3.598     42    
total event_based_risk         3.261    1.680     44    
managing sources               2.720    0.0       1     
splitting sources              2.572    0.0       1     
computing risk                 1.883    0.0       12,364
building hazard                0.354    0.0       44    
compute poes                   0.311    0.0       44    
reading site collection        0.235    0.0       1     
getting hazard                 0.174    0.0       12,364
reading exposure               0.123    0.0       1     
aggregate losses               0.121    0.0       24,112
reading composite source model 0.090    0.0       1     
make contexts                  0.033    0.0       44    
saving ruptures                0.023    0.0       1     
filtering ruptures             0.018    0.0       57    
store source_info              0.015    0.0       1     
saving event loss tables       0.011    0.0       44    
aggregate curves               0.003    0.0       42    
filtering sources              0.002    0.0       1     
============================== ======== ========= ======