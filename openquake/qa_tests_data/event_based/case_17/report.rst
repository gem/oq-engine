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

Expected data transfer for the sources
--------------------------------------
=========================== ========
Number of tasks to generate 2       
Sent data                   17.99 KB
Total received data         9.74 KB 
Maximum received per task   6.69 KB 
=========================== ========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         PointSource  0.975  1         1.910E-04   0.0        0.029    
1            2         PointSource  0.175  1         1.340E-04   0.0        0.009    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.039     0.0       2     
reading composite source model 0.013     0.0       1     
managing sources               0.006     0.0       1     
total compute_gmfs_and_curves  0.005     0.0       3     
saving gmfs                    0.004     0.0       3     
aggregating hcurves            0.003     0.0       3     
saving ruptures                0.002     0.0       1     
make contexts                  0.002     0.0       3     
store source_info              0.002     0.0       1     
aggregate curves               0.002     0.0       5     
compute poes                   0.001     0.0       3     
bulding hazard curves          4.528E-04 0.0       3     
filtering sources              3.250E-04 0.0       2     
reading site collection        5.794E-05 0.0       1     
============================== ========= ========= ======