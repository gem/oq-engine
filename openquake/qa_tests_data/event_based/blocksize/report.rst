QA test for blocksize independence (hazard)
===========================================

num_sites = 2, sitecol = 785 B

Parameters
----------
============================ ==================
calculation_mode             'event_based'     
number_of_logic_tree_samples 1                 
maximum_distance             {'default': 400.0}
investigation_time           5.0               
ses_per_logic_tree_path      1                 
truncation_level             3.0               
rupture_mesh_spacing         10.0              
complex_fault_mesh_spacing   10.0              
width_of_mfd_bin             0.5               
area_source_discretization   10.0              
random_seed                  1024              
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
====== =============== =========== ======================= =================
trt_id gsims           distances   siteparams              ruptparams       
====== =============== =========== ======================= =================
0      ChiouYoungs2008 rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== =============== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008: ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 3           3            277   
================ ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ======
compute_ruptures_max_received_per_task 5563  
compute_ruptures_sent.Monitor          95380 
compute_ruptures_sent.RlzsAssoc        108756
compute_ruptures_sent.SiteCollection   17518 
compute_ruptures_sent.WeightedSequence 527040
compute_ruptures_sent.int              190   
compute_ruptures_tot_received          153512
hazard.input_weight                    560.15
hazard.n_imts                          1     
hazard.n_levels                        4.0   
hazard.n_realizations                  1     
hazard.n_sites                         2     
hazard.n_sources                       0     
hazard.output_weight                   0.1   
====================================== ======

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         AreaSource   175    1,170     8.430E-04   0.308      4.649    
0            2         AreaSource   58     389       7.811E-04   0.099      1.240    
0            3         AreaSource   44     352       7.310E-04   0.080      0.508    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         6.440     0.0       38    
reading composite source model 1.716     0.0       1     
managing sources               0.638     0.0       1     
splitting sources              0.487     0.0       3     
store source_info              0.018     0.0       1     
filtering sources              0.007     0.0       9     
total compute_gmfs_and_curves  0.006     0.0       3     
make contexts                  0.003     0.0       3     
saving gmfs                    0.003     0.0       3     
saving ruptures                0.002     0.0       1     
compute poes                   0.002     0.0       3     
aggregate curves               0.002     0.0       38    
filtering ruptures             0.001     0.0       3     
reading site collection        3.195E-05 0.0       1     
============================== ========= ========= ======