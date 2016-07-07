event based risk
================

gem-tstation:/home/michele/ssd/calc_22577.hdf5 updated Tue May 31 15:37:04 2016

num_sites = 7, sitecol = 1015 B

Parameters
----------
============================ ===============================
calculation_mode             'event_based_risk'             
number_of_logic_tree_samples 0                              
maximum_distance             {'Active Shallow Crust': 200.0}
investigation_time           10000.0                        
ses_per_logic_tree_path      1                              
truncation_level             3.0                            
rupture_mesh_spacing         2.0                            
complex_fault_mesh_spacing   2.0                            
width_of_mfd_bin             0.1                            
area_source_discretization   None                           
random_seed                  24                             
master_seed                  42                             
avg_losses                   False                          
engine_version               '2.0.0-git4fb4450'             
============================ ===============================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
occupants_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       rake mag  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           265          482   
================ ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ============
event_based_risk_max_received_per_task 4,988       
event_based_risk_num_tasks             22          
event_based_risk_sent.assetcol         39,314      
event_based_risk_sent.monitor          57,860      
event_based_risk_sent.riskinput        390,467     
event_based_risk_sent.riskmodel        32,758      
event_based_risk_sent.rlzs_assoc       18,634      
event_based_risk_tot_received          109,466     
hostname                               gem-tstation
require_epsilons                       1           
====================================== ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 265  
Total number of events   392  
Rupture multiplicity     1.479
======================== =====

Maximum memory allocated for the GMFs
-------------------------------------
The largest GMF block is for src_group_id=0, contains 1 IMT(s), 1 realization(s)
and has a size of 10.72 KB / num_tasks

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 1 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 20 tasks = 1.09 KB

Exposure model
--------------
=========== =
#assets     7
#taxonomies 1
=========== =

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
tax1     1.000 0.0    1   1   7         7         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
src_group_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
0            1         SimpleFaultSource 482    15        0.002       0.037      0.680    
============ ========= ================= ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
================= =========== ========== ========= ======
source_class      filter_time split_time calc_time counts
================= =========== ========== ========= ======
SimpleFaultSource 0.002       0.037      0.680     1     
================= =========== ========== ========= ======

Information about the tasks
---------------------------
========================== ===== ====== ===== ===== =========
measurement                mean  stddev min   max   num_tasks
compute_ruptures.time_sec  0.049 0.027  0.019 0.105 14       
compute_ruptures.memory_mb 0.0   0.0    0.0   0.0   14       
event_based_risk.time_sec  0.045 0.019  0.008 0.084 22       
event_based_risk.memory_mb 0.045 0.154  0.0   0.660 22       
========================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total event_based_risk         0.999     0.660     22    
building hazard                0.915     0.0       22    
total compute_ruptures         0.685     0.0       14    
filtering ruptures             0.511     0.0       265   
make contexts                  0.470     0.0       265   
compute poes                   0.435     0.0       265   
saving ruptures                0.210     0.0       1     
building riskinputs            0.073     0.0       1     
managing sources               0.066     0.0       1     
computing riskmodel            0.063     0.0       154   
splitting sources              0.037     0.0       1     
aggregate losses               0.021     0.0       154   
reading composite source model 0.008     0.0       1     
reading exposure               0.007     0.0       1     
store source_info              0.007     0.0       1     
saving event loss tables       0.006     0.0       22    
aggregate curves               0.004     0.0       14    
filtering sources              0.002     0.0       1     
reading site collection        8.106E-06 0.0       1     
============================== ========= ========= ======