Event Based PSHA using Area Source
==================================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ==================
calculation_mode             'event_based'     
number_of_logic_tree_samples 0                 
maximum_distance             {'default': 200.0}
investigation_time           50.0              
ses_per_logic_tree_path      10                
truncation_level             3.0               
rupture_mesh_spacing         2.0               
complex_fault_mesh_spacing   2.0               
width_of_mfd_bin             0.1               
area_source_discretization   5.0               
random_seed                  23                
master_seed                  0                 
concurrent_tasks             40                
============================ ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
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
source_model.xml 0      Active Shallow Crust 1           183          1,230 
================ ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ======
compute_ruptures_max_received_per_task 8747  
compute_ruptures_sent.Monitor          222480
compute_ruptures_sent.RlzsAssoc        293653
compute_ruptures_sent.SiteCollection   45011 
compute_ruptures_sent.WeightedSequence 428006
compute_ruptures_sent.int              515   
compute_ruptures_tot_received          517334
hazard.input_weight                    1230.0
hazard.n_imts                          1     
hazard.n_levels                        19.0  
hazard.n_realizations                  1     
hazard.n_sites                         1     
hazard.n_sources                       0     
hazard.output_weight                   5.0   
====================================== ======

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         AreaSource   1,230  205       8.180E-04   0.048      28       
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         28        1.426     103   
total compute_gmfs_and_curves  0.220     0.312     37    
managing sources               0.170     0.0       1     
saving gmfs                    0.134     0.0       37    
compute poes                   0.110     0.0       183   
make contexts                  0.086     0.0       183   
filtering ruptures             0.079     0.0       183   
saving ruptures                0.053     0.0       1     
reading composite source model 0.051     0.0       1     
splitting sources              0.048     0.0       1     
aggregate curves               0.032     0.0       140   
aggregating hcurves            0.018     0.0       37    
bulding hazard curves          0.007     0.0       37    
store source_info              0.005     0.0       1     
filtering sources              8.180E-04 0.0       1     
reading site collection        2.909E-05 0.0       1     
============================== ========= ========= ======