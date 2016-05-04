Virtual Island - City C, 2 SES, grid=0.1
========================================

gem-tstation:/home/michele/ssd/calc_12617.hdf5 updated Wed May  4 04:54:33 2016

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
oqlite_version               '0.13.0-git02c4b55'
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
event_based_risk_max_received_per_task 4030          
event_based_risk_num_tasks             44            
event_based_risk_sent.assetcol         978428        
event_based_risk_sent.monitor          116072        
event_based_risk_sent.riskinput        2204291       
event_based_risk_sent.riskmodel        836264        
event_based_risk_sent.rlzs_assoc       133408        
event_based_risk_tot_received          177057        
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

========== ===== ====== === === ========= ==========
taxonomy   mean  stddev min max num_sites num_assets
A-SPSB-1   1.250 0.463  1   2   8         10        
MC-RCSB-1  1.286 0.561  1   3   21        27        
MC-RLSB-2  1.256 0.880  1   6   39        49        
MR-RCSB-2  1.456 0.799  1   6   171       249       
MR-SLSB-1  1.000 0.0    1   1   5         5         
MS-FLSB-2  1.250 0.452  1   2   12        15        
MS-SLSB-1  1.545 0.934  1   4   11        17        
PCR-RCSM-5 1.000 0.0    1   1   2         2         
PCR-SLSB-1 1.000 0.0    1   1   3         3         
W-FLFB-2   1.222 0.502  1   3   54        66        
W-SLFB-1   1.265 0.520  1   3   83        105       
*ALL*      1.950 1.306  1   10  281       548       
========== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ================== ====== ========= =========== ========== =========
trt_model_id source_id source_class       weight split_num filter_time split_time calc_time
============ ========= ================== ====== ========= =========== ========== =========
0            F         ComplexFaultSource 2,558  1,119     0.002       2.698      3.462    
============ ========= ================== ====== ========= =========== ========== =========

Information about the tasks
---------------------------
========================== ===== ====== ===== ===== =========
measurement                mean  stddev min   max   num_tasks
compute_ruptures.time_sec  0.083 0.186  0.001 0.597 42       
compute_ruptures.memory_mb 0.002 0.005  0.0   0.027 42       
event_based_risk.time_sec  0.068 0.017  0.043 0.106 44       
event_based_risk.memory_mb 0.113 0.089  0.0   0.277 44       
========================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ======== ========= ======
operation                      time_sec memory_mb counts
============================== ======== ========= ======
total compute_ruptures         3.484    0.027     42    
total event_based_risk         2.972    0.277     44    
managing sources               2.808    0.0       1     
splitting sources              2.698    0.0       1     
building hazard                1.280    0.0       44    
computing riskmodel            0.826    0.0       17,996
compute poes                   0.351    0.0       44    
reading site collection        0.288    0.0       1     
aggregate losses               0.135    0.0       17,996
reading composite source model 0.129    0.0       1     
reading exposure               0.122    0.0       1     
saving ruptures                0.043    0.0       1     
make contexts                  0.034    0.0       44    
store source_info              0.025    0.0       1     
filtering ruptures             0.018    0.0       57    
saving event loss tables       0.011    0.0       44    
aggregate curves               0.005    0.0       42    
filtering sources              0.002    0.0       1     
============================== ======== ========= ======