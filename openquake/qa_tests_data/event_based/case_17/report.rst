Event Based Hazard QA Test, Case 17
===================================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ==================
calculation_mode             'event_based'     
number_of_logic_tree_samples 5                 
maximum_distance             {'default': 200.0}
investigation_time           1.0               
ses_per_logic_tree_path      3                 
truncation_level             2.0               
rupture_mesh_spacing         1.0               
complex_fault_mesh_spacing   1.0               
width_of_mfd_bin             1.0               
area_source_discretization   10.0              
random_seed                  106               
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
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ========================================== =============== ================
smlt_path weight source_model_file                          gsim_logic_tree num_realizations
========= ====== ========================================== =============== ================
b1        0.200  `source_model_1.xml <source_model_1.xml>`_ trivial(0)      1/1             
b2        0.200  `source_model_2.xml <source_model_2.xml>`_ trivial(1)      4/4             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============== ========= ========== ==========
trt_id gsims          distances siteparams ruptparams
====== ============== ========= ========== ==========
1      SadighEtAl1997 rrup      vs30       rake mag  
====== ============== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=5)
  1,SadighEtAl1997: ['<1,b2,b1,w=0.2>', '<2,b2,b1,w=0.2>', '<3,b2,b1,w=0.2>', '<4,b2,b1,w=0.2>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ======
source_model       trt_id trt                  num_sources eff_ruptures weight
================== ====== ==================== =========== ============ ======
source_model_2.xml 1      Active Shallow Crust 1           3            0.175 
================== ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ==================
compute_ruptures_max_received_per_task 7113              
compute_ruptures_sent.Monitor          5068              
compute_ruptures_sent.RlzsAssoc        9458              
compute_ruptures_sent.SiteCollection   874               
compute_ruptures_sent.WeightedSequence 3055              
compute_ruptures_sent.int              10                
compute_ruptures_tot_received          10380             
hazard.input_weight                    1.6750000000000003
hazard.n_imts                          1                 
hazard.n_levels                        3.0               
hazard.n_realizations                  5                 
hazard.n_sites                         1                 
hazard.n_sources                       0                 
hazard.output_weight                   0.15              
====================================== ==================

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         PointSource  0.975  1         9.584E-05   0.0        0.023    
1            2         PointSource  0.175  1         6.008E-05   0.0        0.006    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.030     0.0       2     
total compute_gmfs_and_curves  0.006     0.0       3     
reading composite source model 0.006     0.0       1     
store source_info              0.005     0.0       1     
managing sources               0.003     0.0       1     
make contexts                  0.003     0.0       3     
saving gmfs                    0.002     0.0       3     
saving ruptures                0.002     0.0       1     
aggregating hcurves            0.002     0.0       3     
compute poes                   0.001     0.0       3     
filtering ruptures             0.001     0.0       3     
aggregate curves               0.001     0.0       5     
bulding hazard curves          6.118E-04 0.0       3     
filtering sources              1.559E-04 0.0       2     
reading site collection        3.886E-05 0.0       1     
============================== ========= ========= ======