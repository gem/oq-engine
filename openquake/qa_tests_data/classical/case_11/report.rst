Classical Hazard QA Test, Case 11
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
b1_b2     0.200  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b3     0.600  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b4     0.200  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============== ========= ========== ==========
trt_id gsims          distances siteparams ruptparams
====== ============== ========= ========== ==========
0      SadighEtAl1997 rrup      vs30       rake mag  
1      SadighEtAl1997 rrup      vs30       rake mag  
2      SadighEtAl1997 rrup      vs30       rake mag  
====== ============== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(3)
  0,SadighEtAl1997: ['<0,b1_b2,b1,w=0.2>']
  1,SadighEtAl1997: ['<1,b1_b3,b1,w=0.6>']
  2,SadighEtAl1997: ['<2,b1_b4,b1,w=0.2>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============ ======
source_model     trt_id trt                  num_sources num_ruptures eff_ruptures weight
================ ====== ==================== =========== ============ ============ ======
source_model.xml 0      active shallow crust 1           3500         3500         87.5  
source_model.xml 1      active shallow crust 1           3000         3000         75.0  
source_model.xml 2      active shallow crust 1           2500         2500         62.5  
================ ====== ==================== =========== ============ ============ ======

=============== =====
#TRT models     3    
#sources        3    
#tot_ruptures   9000 
#eff_ruptures   9000 
filtered_weight 225.0
=============== =====

Expected data transfer for the sources
--------------------------------------
=========================== =======
Number of tasks to generate 3      
Sent data                   26.5 KB
=========================== =======

Slowest sources
---------------
============ ========= ============ ====== ========= =========== =========== =========
trt_model_id source_id source_class weight split_num filter_time split_time  calc_time
============ ========= ============ ====== ========= =========== =========== =========
0            1         PointSource  87.5   1         0.00590706  2.71797e-05 0.0      
1            1         PointSource  75.0   1         0.00479317  2.40803e-05 0.0      
2            1         PointSource  62.5   1         0.00402522  2.38419e-05 0.0      
============ ========= ============ ====== ========= =========== =========== =========