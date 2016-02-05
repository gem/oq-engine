QA test for disaggregation case_1, taken from the disagg demo
=============================================================

num_sites = 2, sitecol = 730 B

Parameters
----------
============================ ==============
calculation_mode             disaggregation
number_of_logic_tree_samples 0             
maximum_distance             200.0         
investigation_time           50.0          
ses_per_logic_tree_path      1             
truncation_level             3.0           
rupture_mesh_spacing         5.0           
complex_fault_mesh_spacing   5.0           
width_of_mfd_bin             0.2           
area_source_discretization   10.0          
random_seed                  9000          
master_seed                  0             
concurrent_tasks             16            
============================ ==============

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

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============ =======
source_model     trt_id trt                  num_sources num_ruptures eff_ruptures weight 
================ ====== ==================== =========== ============ ============ =======
source_model.xml 0      Active Shallow Crust 4           2236         2236         817.375
================ ====== ==================== =========== ============ ============ =======

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 14       
Sent data                   182.79 KB
=========================== =========

Slowest sources
---------------
============ ========= ================== ====== ========= =========== ========== =========
trt_model_id source_id source_class       weight split_num filter_time split_time calc_time
============ ========= ================== ====== ========= =========== ========== =========
0            4         ComplexFaultSource 164.0  29        0.00206995  0.258712   0.0      
0            3         SimpleFaultSource  617.0  83        0.00298786  0.084249   0.0      
0            2         AreaSource         36.0   1         0.00124598  0.0        0.0      
0            1         PointSource        0.375  1         0.000191927 0.0        0.0      
============ ========= ================== ====== ========= =========== ========== =========