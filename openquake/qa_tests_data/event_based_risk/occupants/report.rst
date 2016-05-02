event based risk
================

gem-tstation:/home/michele/ssd/calc_990.hdf5 updated Thu Apr 28 15:38:46 2016

num_sites = 7, sitecol = 1015 B

Parameters
----------
============================ ===================
calculation_mode             'event_based_risk' 
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
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
oqlite_version               '0.13.0-git93d6f64'
============================ ===================

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
====== ================= ========= ========== ==========
trt_id gsims             distances siteparams ruptparams
====== ================= ========= ========== ==========
0      BooreAtkinson2008 rjb       vs30       rake mag  
====== ================= ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008: ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           265          482   
================ ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ==============
event_based_risk_max_received_per_task 6942          
event_based_risk_num_tasks             47            
event_based_risk_sent.assetcol         83989         
event_based_risk_sent.monitor          122811        
event_based_risk_sent.riskinput        420098        
event_based_risk_sent.riskmodel        86527         
event_based_risk_sent.rlzs_assoc       124080        
event_based_risk_tot_received          325957        
hostname                               'gem-tstation'
require_epsilons                       True          
====================================== ==============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 265  
Total number of events   392  
Rupture multiplicity     1.479
======================== =====

Maximum memory allocated for the GMFs
-------------------------------------
The largest GMF block is for trt_model_id=0, contains 1 IMT(s), 1 realization(s)
and has a size of 10.72 KB / num_tasks

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 1 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 40 tasks = 2.19 KB

Exposure model
--------------
=========== =
#assets     7
#taxonomies 1
=========== =

======== =======
Taxonomy #Assets
======== =======
tax1     7      
======== =======

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
trt_model_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
0            1         SimpleFaultSource 482    15        0.003       0.083      2.497    
============ ========= ================= ====== ========= =========== ========== =========

Information about the tasks
---------------------------
========================== ===== ===== ===== ======
measurement                min   max   mean  stddev
compute_ruptures.time_sec  0.076 0.292 0.167 0.068 
compute_ruptures.memory_mb 0.020 0.582 0.185 0.157 
event_based_risk.time_sec  0.016 0.109 0.062 0.026 
event_based_risk.memory_mb 0.0   1.355 0.383 0.447 
========================== ===== ===== ===== ======

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total event_based_risk         2.898     1.355     47    
total compute_ruptures         2.503     0.582     15    
building hazard                2.098     0.0       47    
filtering ruptures             1.906     0.0       265   
make contexts                  1.503     0.0       265   
computing risk                 0.701     0.0       329   
compute poes                   0.587     0.0       265   
saving ruptures                0.352     0.0       1     
managing sources               0.170     0.0       1     
splitting sources              0.083     0.0       1     
aggregate losses               0.044     0.0       329   
saving event loss tables       0.014     0.0       47    
getting hazard                 0.012     0.0       329   
reading composite source model 0.012     0.0       1     
reading exposure               0.010     0.0       1     
store source_info              0.008     0.0       1     
aggregate curves               0.006     0.0       15    
filtering sources              0.003     0.0       1     
reading site collection        1.001E-05 0.0       1     
============================== ========= ========= ======