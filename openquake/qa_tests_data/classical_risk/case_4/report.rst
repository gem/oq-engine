Classical Hazard-Risk QA test 4
===============================

num_sites = 6, sitecol = 969 B

Parameters
----------
============================ ==================
calculation_mode             'classical'       
number_of_logic_tree_samples 0                 
maximum_distance             {'default': 200.0}
investigation_time           50.0              
ses_per_logic_tree_path      1                 
truncation_level             3.0               
rupture_mesh_spacing         5.0               
complex_fault_mesh_spacing   5.0               
width_of_mfd_bin             0.2               
area_source_discretization   10.0              
random_seed                  23                
master_seed                  0                 
concurrent_tasks             16                
sites_per_tile               1000              
============================ ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job_haz.ini <job_haz.ini>`_                                
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ simple(2)       2/2             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =============================== =========== ======================= =================
trt_id gsims                           distances   siteparams              ruptparams       
====== =============================== =========== ======================= =================
0      AkkarBommer2010 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== =============================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AkkarBommer2010: ['<0,b1,b1,w=0.4>']
  0,ChiouYoungs2008: ['<1,b1,b2,w=0.6>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 2           6,405        160   
================ ====== ==================== =========== ============ ======

Expected data transfer for the sources
--------------------------------------
=========================== ========
Number of tasks to generate 2       
Sent data                   16.95 KB
=========================== ========

Exposure model
--------------
=========== =
#assets     6
#taxonomies 2
=========== =

======== =======
Taxonomy #Assets
======== =======
A        1      
W        5      
======== =======

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            376       AreaSource   55     1         7.830E-04   0.0        0.0      
0            231       AreaSource   104    1         6.979E-04   0.0        0.0      
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 2.586     0.0       1     
managing sources               0.032     0.0       1     
filtering sources              0.029     0.0       39    
reading exposure               0.004     0.0       1     
total count_eff_ruptures       0.003     0.0       2     
store source_info              2.241E-04 0.0       1     
aggregate curves               3.314E-05 0.0       2     
reading site collection        9.060E-06 0.0       1     
============================== ========= ========= ======