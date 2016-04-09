Event Based QA Test, Case 12
============================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ==================
calculation_mode             'event_based'     
number_of_logic_tree_samples 0                 
maximum_distance             {'default': 200.0}
investigation_time           1.0               
ses_per_logic_tree_path      3500              
truncation_level             2.0               
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
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1,1)    1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= ========= ========== ==========
trt_id gsims             distances siteparams ruptparams
====== ================= ========= ========== ==========
0      SadighEtAl1997    rrup      vs30       rake mag  
1      BooreAtkinson2008 rjb       vs30       rake mag  
====== ================= ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,SadighEtAl1997: ['<0,b1,b1_b2,w=1.0>']
  1,BooreAtkinson2008: ['<0,b1,b1_b2,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           1            0.025 
source_model.xml 1      Stable Continental   1           1            0.025 
================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   2    
filtered_weight 0.050
=============== =====

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 2        
Sent data                   15.22 KB 
Total received data         211.62 KB
Maximum received per task   108.24 KB
=========================== =========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         PointSource  0.025  1         1.428E-04   0.0        0.052    
1            2         PointSource  0.025  1         1.590E-04   0.0        0.033    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.086     0.043     2     
saving ruptures                0.025     0.0       1     
total compute_gmfs_and_curves  0.019     0.0       2     
bulding hazard curves          0.014     0.0       2     
reading composite source model 0.008     0.0       1     
managing sources               0.004     0.0       1     
saving gmfs                    0.003     0.0       2     
compute poes                   0.002     0.0       2     
aggregate curves               0.002     0.0       4     
store source_info              0.002     0.0       1     
aggregating hcurves            0.002     0.0       2     
make contexts                  0.001     0.0       2     
filtering sources              3.018E-04 0.0       2     
reading site collection        5.198E-05 0.0       1     
============================== ========= ========= ======