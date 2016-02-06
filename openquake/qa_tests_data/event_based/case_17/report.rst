Event Based Hazard QA Test, Case 17
===================================

num_sites = 1, sitecol = 684 B

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 5          
maximum_distance             200        
investigation_time           1000       
ses_per_logic_tree_path      3          
truncation_level             2.0000     
rupture_mesh_spacing         1.0000     
complex_fault_mesh_spacing   1.0000     
width_of_mfd_bin             1.0000     
area_source_discretization   10         
random_seed                  106        
master_seed                  0          
concurrent_tasks             16         
============================ ===========

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
b1        0.2000 `source_model_1.xml <source_model_1.xml>`_ trivial(1)      1/1             
b2        0.2000 `source_model_2.xml <source_model_2.xml>`_ trivial(1)      4/4             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============== ========= ========== ==========
trt_id gsims          distances siteparams ruptparams
====== ============== ========= ========== ==========
0      SadighEtAl1997 rrup      vs30       rake mag  
1      SadighEtAl1997 rrup      vs30       rake mag  
====== ============== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(2)
  0,SadighEtAl1997: ['<0,b1,b1,w=0.2>']
  1,SadighEtAl1997: ['<1,b2,b1,w=0.2>', '<2,b2,b1,w=0.2>', '<3,b2,b1,w=0.2>', '<4,b2,b1,w=0.2>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b1        active shallow crust 2           
1   b2        active shallow crust 2,838       
2   b2        active shallow crust 2,672       
3   b2        active shallow crust 2,770       
4   b2        active shallow crust 2,665       
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
0           0           
1           1           
2           2           
3           3           
4           4           
=========== ============

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 2        
Sent data                   16.37 KB 
Total received data         894.29 KB
Maximum received per task   890.23 KB
=========================== =========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
1            2         PointSource  0.1750 1         0.0002      0.0        0.1143   
0            1         PointSource  0.9750 1         0.0003      0.0        0.0305   
============ ========= ============ ====== ========= =========== ========== =========