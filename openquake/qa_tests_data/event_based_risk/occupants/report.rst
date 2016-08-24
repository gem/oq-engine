event based risk
================

gem-tstation:/home/michele/ssd/calc_43304.hdf5 updated Wed Aug 24 20:17:22 2016

num_sites = 7, sitecol = 1015 B

Parameters
----------
============================ ================================
calculation_mode             'event_based_risk'              
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
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
engine_version               '2.1.0-git50eb989'              
============================ ================================

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
compute_ruptures_max_received_per_task 35,146      
compute_ruptures_num_tasks             13          
compute_ruptures_sent.monitor          10,465      
compute_ruptures_sent.rlzs_by_gsim     6,838       
compute_ruptures_sent.sitecol          7,189       
compute_ruptures_sent.sources          18,407      
compute_ruptures_tot_received          291,831     
hazard.input_weight                    482         
hazard.n_imts                          1           
hazard.n_levels                        1.000       
hazard.n_realizations                  1           
hazard.n_sites                         7           
hazard.n_sources                       1           
hazard.output_weight                   7.000       
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
=============== ========
#assets         7       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
tax1     1.000 0.0    1   1   7         7         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class      weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ================= ====== ========= =========== ========== ============= ============= =========
0            1         SimpleFaultSource 482    15        0.002       0.033      0.840         0.121         15       
============ ========= ================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================= =========== ========== ============= ============= ========= ======
source_class      filter_time split_time cum_calc_time max_calc_time num_tasks counts
================= =========== ========== ============= ============= ========= ======
SimpleFaultSource 0.002       0.033      0.840         0.121         15        1     
================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
========================== ===== ====== ===== ===== =========
measurement                mean  stddev min   max   num_tasks
compute_ruptures.time_sec  0.065 0.027  0.031 0.121 13       
compute_ruptures.memory_mb 0.0   0.0    0.0   0.0   13       
========================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.842     0.0       13    
filtering ruptures             0.623     0.0       265   
saving ruptures                0.179     0.0       1     
managing sources               0.050     0.0       1     
splitting sources              0.033     0.0       1     
reading composite source model 0.007     0.0       1     
store source_info              0.007     0.0       1     
aggregate curves               0.006     0.0       13    
reading exposure               0.005     0.0       1     
filtering sources              0.002     0.0       1     
reading site collection        9.060E-06 0.0       1     
============================== ========= ========= ======