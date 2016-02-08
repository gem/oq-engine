PEB QA test 2
=============

num_sites = 3, sitecol = 776 B

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             100        
investigation_time           50         
ses_per_logic_tree_path      20         
truncation_level             3.000      
rupture_mesh_spacing         5.000      
complex_fault_mesh_spacing   5.000      
width_of_mfd_bin             0.300      
area_source_discretization   10         
random_seed                  23         
master_seed                  0          
concurrent_tasks             16         
============================ ===========

Input files
-----------
======================== ==============================================================
Name                     File                                                          
======================== ==============================================================
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                  
job_ini                  `job_haz.ini <job_haz.ini>`_                                  
source                   `source_model.xml <source_model.xml>`_                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_  
structural_vulnerability `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_
======================== ==============================================================

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

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b1        Active Shallow Crust 26          
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
0           0           
=========== ============

Expected data transfer for the sources
--------------------------------------
=========================== ========
Number of tasks to generate 1       
Sent data                   7.63 KB 
Total received data         10.51 KB
Maximum received per task   10.51 KB
=========================== ========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            3         PointSource  0.150  1         1.121E-04   0.0        0.005    
0            2         PointSource  0.150  1         1.171E-04   0.0        0.004    
0            1         PointSource  0.150  1         1.678E-04   0.0        0.004    
============ ========= ============ ====== ========= =========== ========== =========