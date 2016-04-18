Event-Based Hazard QA Test, Case 4
==================================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ==================
calculation_mode             'event_based'     
number_of_logic_tree_samples 0                 
maximum_distance             {'default': 200.0}
investigation_time           1.0               
ses_per_logic_tree_path      50                
truncation_level             0.0               
rupture_mesh_spacing         1.0               
complex_fault_mesh_spacing   1.0               
width_of_mfd_bin             1.0               
area_source_discretization   10.0              
random_seed                  1066              
master_seed                  0                 
concurrent_tasks             40                
============================ ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
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
====== ============== ========= ========== ==========
trt_id gsims          distances siteparams ruptparams
====== ============== ========= ========== ==========
0      SadighEtAl1997 rrup      vs30       rake mag  
====== ============== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997: ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           10           10    
================ ====== ==================== =========== ============ ======

Informational data
------------------
====================================== =====
compute_ruptures_max_received_per_task 11464
compute_ruptures_sent.Monitor          2560 
compute_ruptures_sent.RlzsAssoc        2874 
compute_ruptures_sent.SiteCollection   437  
compute_ruptures_sent.WeightedSequence 1261 
compute_ruptures_sent.int              5    
compute_ruptures_tot_received          11464
hazard.input_weight                    10.0 
hazard.n_imts                          1    
hazard.n_levels                        3.0  
hazard.n_realizations                  1    
hazard.n_sites                         1    
hazard.n_sources                       0    
hazard.output_weight                   0.5  
====================================== =====

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
trt_model_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
0            1         SimpleFaultSource 10     1         0.002       0.003      0.019    
============ ========= ================= ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_gmfs_and_curves  0.038     0.0       10    
make contexts                  0.027     0.0       10    
total compute_ruptures         0.020     0.0       1     
filtering ruptures             0.011     0.0       10    
saving gmfs                    0.010     0.0       10    
reading composite source model 0.008     0.0       1     
managing sources               0.007     0.0       1     
aggregating hcurves            0.007     0.0       10    
store source_info              0.007     0.0       1     
saving ruptures                0.005     0.0       1     
splitting sources              0.003     0.0       1     
compute poes                   0.003     0.0       10    
bulding hazard curves          0.002     0.0       10    
filtering sources              0.002     0.0       1     
aggregate curves               0.001     0.0       11    
reading site collection        3.910E-05 0.0       1     
============================== ========= ========= ======