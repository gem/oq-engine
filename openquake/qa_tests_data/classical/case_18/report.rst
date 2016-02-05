Demo Classical PSHA for Vancouver Schools
=========================================

num_sites = 3, sitecol = 776 B

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             400.0    
investigation_time           1.0      
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         5.0      
complex_fault_mesh_spacing   5.0      
width_of_mfd_bin             0.1      
area_source_discretization   50.0     
random_seed                  23       
master_seed                  0        
concurrent_tasks             16       
sites_per_tile               1000     
============================ =========

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `nbc_asc_logic_tree.xml <nbc_asc_logic_tree.xml>`_          
job_ini                 `job.ini <job.ini>`_                                        
sites                   `vancouver_school_sites.csv <vancouver_school_sites.csv>`_  
source                  `vancouver_area_source.xml <vancouver_area_source.xml>`_    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ======================================================== =============== ================
smlt_path weight source_model_file                                        gsim_logic_tree num_realizations
========= ====== ======================================================== =============== ================
b1        1.00   `vancouver_area_source.xml <vancouver_area_source.xml>`_ simple(3)       3/3             
========= ====== ======================================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========= ========= ========== ==========
trt_id gsims     distances siteparams ruptparams
====== ========= ========= ========== ==========
0      GMPETable rhypo                mag       
====== ========= ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,GMPETable: ['<0,b1,b11,w=0.16>', '<1,b1,b12,w=0.68>', '<2,b1,b13,w=0.16>']>

Number of ruptures per tectonic region type
-------------------------------------------
========================= ====== ==================== =========== ============ ============ ======
source_model              trt_id trt                  num_sources num_ruptures eff_ruptures weight
========================= ====== ==================== =========== ============ ============ ======
vancouver_area_source.xml 0      Active Shallow Crust 1           2430         2430         60.75 
========================= ====== ==================== =========== ============ ============ ======

Expected data transfer for the sources
--------------------------------------
=========================== =======
Number of tasks to generate 30     
Sent data                   4.79 MB
=========================== =======

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            VICM      AreaSource   60.75  30        0.00128603  0.0106101  0.0      
============ ========= ============ ====== ========= =========== ========== =========