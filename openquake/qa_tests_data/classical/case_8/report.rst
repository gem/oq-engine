Classical Hazard QA Test, Case 8
================================

num_sites = 1, sitecol = 684 B

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200      
investigation_time           1.0000   
ses_per_logic_tree_path      1        
truncation_level             0.0      
rupture_mesh_spacing         0.0100   
complex_fault_mesh_spacing   0.0100   
width_of_mfd_bin             0.0010   
area_source_discretization   10       
random_seed                  1,066    
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
b1_b2     0.300  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b3     0.300  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b4     0.400  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
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
  0,SadighEtAl1997: ['<0,b1_b2,b1,w=0.3>']
  1,SadighEtAl1997: ['<1,b1_b3,b1,w=0.3>']
  2,SadighEtAl1997: ['<2,b1_b4,b1,w=0.4>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           3,000        75    
source_model.xml 1      Active Shallow Crust 1           3,000        75    
source_model.xml 2      Active Shallow Crust 1           3,000        75    
================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     3    
#sources        3    
#eff_ruptures   9,000
filtered_weight 225  
=============== =====

Expected data transfer for the sources
--------------------------------------
=========================== ========
Number of tasks to generate 3       
Sent data                   26.32 KB
=========================== ========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         PointSource  75     1         0.0047      2.1935E-05 0.0      
1            1         PointSource  75     1         0.0043      1.5020E-05 0.0      
2            1         PointSource  75     1         0.0043      1.5020E-05 0.0      
============ ========= ============ ====== ========= =========== ========== =========