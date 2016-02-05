Event Based PSHA using Area Source
==================================

num_sites = 1, sitecol = 684 B

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             200.0      
investigation_time           50.0       
ses_per_logic_tree_path      10         
truncation_level             3.0        
rupture_mesh_spacing         2.0        
complex_fault_mesh_spacing   2.0        
width_of_mfd_bin             0.1        
area_source_discretization   5.0        
random_seed                  23         
master_seed                  0          
concurrent_tasks             16         
============================ ===========

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
b1        1.00   `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
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

  <RlzsAssoc(1)
  0,BooreAtkinson2008: ['<0,b1,b1,w=1.0>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b1        Active Shallow Crust 184         
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
0           0           
=========== ============

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 18       
Sent data                   356.6 KB 
Total received data         185.85 KB
Maximum received per task   15.5 KB  
=========================== =========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         AreaSource   1230.0 205       0.00123906  0.0648618  33.3806  
============ ========= ============ ====== ========= =========== ========== =========