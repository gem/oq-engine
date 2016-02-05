QA test for blocksize independence (hazard)
===========================================

num_sites = 2, sitecol = 730 B

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 1          
maximum_distance             400.0      
investigation_time           5.0        
ses_per_logic_tree_path      1          
truncation_level             3.0        
rupture_mesh_spacing         10.0       
complex_fault_mesh_spacing   10.0       
width_of_mfd_bin             0.5        
area_source_discretization   10.0       
random_seed                  1024       
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
b1        1.0    `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
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

  <RlzsAssoc(1)
  0,ChiouYoungs2008: ['<0,b1,b1,w=1.0>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b1        Active Shallow Crust 3           
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
Number of tasks to generate 8        
Sent data                   532.92 KB
Total received data         43.62 KB 
Maximum received per task   7.78 KB  
=========================== =========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         AreaSource   175.5  1170      0.00109506  0.407942   5.45753  
0            2         AreaSource   58.35  389       0.00119805  0.131387   1.39336  
0            3         AreaSource   44.0   352       0.00114608  0.107548   0.760117 
============ ========= ============ ====== ========= =========== ========== =========