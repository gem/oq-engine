QA test for disaggregation case_1, taken from the disagg demo
=============================================================

num_sites = 2, sitecol = 730 B

Parameters
----------
============================ ==============
calculation_mode             disaggregation
number_of_logic_tree_samples 0             
maximum_distance             200           
investigation_time           50            
ses_per_logic_tree_path      1             
truncation_level             3.000         
rupture_mesh_spacing         5.000         
complex_fault_mesh_spacing   5.000         
width_of_mfd_bin             0.200         
area_source_discretization   10            
random_seed                  9,000         
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

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008: ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 4           2,236        817   
================ ====== ==================== =========== ============ ======

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 14       
Sent data                   182.53 KB
=========================== =========

Slowest sources
---------------
============ ========= ================== ====== ========= =========== ========== =========
trt_model_id source_id source_class       weight split_num filter_time split_time calc_time
============ ========= ================== ====== ========= =========== ========== =========
0            4         ComplexFaultSource 164    29        0.002       0.224      0.0      
0            3         SimpleFaultSource  617    83        0.003       0.075      0.0      
0            2         AreaSource         36     1         0.001       0.0        0.0      
0            1         PointSource        0.375  1         1.740E-04   0.0        0.0      
============ ========= ================== ====== ========= =========== ========== =========