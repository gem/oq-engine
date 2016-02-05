Classical Hazard QA Test, Case 10
=================================

num_sites = 1, sitecol = 684 B

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           1.0      
ses_per_logic_tree_path      1        
truncation_level             0.0      
rupture_mesh_spacing         0.01     
complex_fault_mesh_spacing   0.01     
width_of_mfd_bin             0.001    
area_source_discretization   10.0     
random_seed                  1066     
master_seed                  0        
concurrent_tasks             16       
sites_per_tile               1000     
============================ =========

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
b1_b2     0.500  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b3     0.500  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

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
  0,SadighEtAl1997: ['<0,b1_b2,b1,w=0.5>']
  1,SadighEtAl1997: ['<1,b1_b3,b1,w=0.5>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============ ======
source_model     trt_id trt                  num_sources num_ruptures eff_ruptures weight
================ ====== ==================== =========== ============ ============ ======
source_model.xml 0      active shallow crust 1           3000         3000         75.0  
source_model.xml 1      active shallow crust 1           3000         3000         75.0  
================ ====== ==================== =========== ============ ============ ======

=============== =====
#TRT models     2    
#sources        2    
#tot_ruptures   6000 
#eff_ruptures   6000 
filtered_weight 150.0
=============== =====

Expected data transfer for the sources
--------------------------------------
=========================== ========
Number of tasks to generate 2       
Sent data                   14.75 KB
=========================== ========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== =========== =========
trt_model_id source_id source_class weight split_num filter_time split_time  calc_time
============ ========= ============ ====== ========= =========== =========== =========
0            1         PointSource  75.0   1         0.00466299  2.28882e-05 0.0      
1            1         PointSource  75.0   1         0.00434399  1.38283e-05 0.0      
============ ========= ============ ====== ========= =========== =========== =========