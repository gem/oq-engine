Classical Hazard QA Test, Case 4
================================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ==================
calculation_mode             'classical'       
number_of_logic_tree_samples 0                 
maximum_distance             {'default': 200.0}
investigation_time           1.0               
ses_per_logic_tree_path      1                 
truncation_level             0.0               
rupture_mesh_spacing         0.01              
complex_fault_mesh_spacing   0.01              
width_of_mfd_bin             1.0               
area_source_discretization   10.0              
random_seed                  1066              
master_seed                  0                 
concurrent_tasks             40                
sites_per_tile               1000              
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
source_model.xml 0      Active Shallow Crust 1           901          901   
================ ====== ==================== =========== ============ ======

Expected data transfer for the sources
--------------------------------------
=========================== =======
Number of tasks to generate 1      
Sent data                   6.59 KB
=========================== =======

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
trt_model_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
0            1         SimpleFaultSource 901    1         0.001       0.524      0.0      
============ ========= ================= ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.531     0.0       1     
managing sources               0.527     0.0       1     
splitting sources              0.524     0.0       1     
filtering sources              0.001     0.0       1     
total count_eff_ruptures       3.271E-04 0.0       1     
store source_info              2.489E-04 0.0       1     
reading site collection        3.815E-05 0.0       1     
aggregate curves               2.003E-05 0.0       1     
============================== ========= ========= ======