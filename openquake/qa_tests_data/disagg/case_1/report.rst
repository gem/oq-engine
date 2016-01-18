QA test for disaggregation case_1, taken from the disagg demo
=============================================================

num_sites = 2, sitecol = 461 B

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
concurrent_tasks             64            
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
================ ====== ==================== =========== ============ =======
source_model     trt_id trt                  num_sources num_ruptures weight 
================ ====== ==================== =========== ============ =======
source_model.xml 0      Active Shallow Crust 2236        2236         817.375
================ ====== ==================== =========== ============ =======

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 26       
Sent data                   270.04 KB
Total received data         53.17 KB 
Maximum received per task   2.04 KB  
=========================== =========