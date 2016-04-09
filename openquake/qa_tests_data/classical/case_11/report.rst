Classical Hazard QA Test, Case 11
=================================

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
width_of_mfd_bin             0.001             
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

  <RlzsAssoc(size=3, rlzs=3)
  0,SadighEtAl1997: ['<0,b1_b2,b1,w=0.2>']
  1,SadighEtAl1997: ['<1,b1_b3,b1,w=0.6>']
  2,SadighEtAl1997: ['<2,b1_b4,b1,w=0.2>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           3,500        87    
source_model.xml 1      Active Shallow Crust 1           3,000        75    
source_model.xml 2      Active Shallow Crust 1           2,500        62    
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
Sent data                   28.39 KB
=========================== ========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         PointSource  87     1         0.005       2.193E-05  0.0      
1            1         PointSource  75     1         0.004       1.717E-05  0.0      
2            1         PointSource  62     1         0.003       1.502E-05  0.0      
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.023     0.0       1     
managing sources               0.019     0.0       1     
filtering sources              0.013     0.0       3     
total count_eff_ruptures       7.613E-04 0.0       3     
store source_info              4.799E-04 0.0       1     
aggregate curves               1.142E-04 0.0       3     
splitting sources              5.412E-05 0.0       3     
reading site collection        4.411E-05 0.0       1     
============================== ========= ========= ======