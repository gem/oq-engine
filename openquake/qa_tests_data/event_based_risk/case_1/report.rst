PEB QA test 1
=============

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ==================
calculation_mode             'event_based'     
number_of_logic_tree_samples 0                 
maximum_distance             {'default': 100.0}
investigation_time           50.0              
ses_per_logic_tree_path      20                
truncation_level             3.0               
rupture_mesh_spacing         5.0               
complex_fault_mesh_spacing   5.0               
width_of_mfd_bin             0.3               
area_source_discretization   10.0              
random_seed                  23                
master_seed                  0                 
concurrent_tasks             40                
============================ ==================

Input files
-----------
=========================== ====================================================================
Name                        File                                                                
=========================== ====================================================================
contents_vulnerability      `vulnerability_model_coco.xml <vulnerability_model_coco.xml>`_      
gsim_logic_tree             `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                        
job_ini                     `job_haz.ini <job_haz.ini>`_                                        
nonstructural_vulnerability `vulnerability_model_nonstco.xml <vulnerability_model_nonstco.xml>`_
source                      `source_model.xml <source_model.xml>`_                              
source_model_logic_tree     `source_model_logic_tree.xml <source_model_logic_tree.xml>`_        
structural_vulnerability    `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_      
=========================== ====================================================================

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
  0,AkkarBommer2010: ['<1,b1,b2,w=0.5>']
  0,ChiouYoungs2008: ['<0,b1,b1,w=0.5>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 3           8            0.450 
================ ====== ==================== =========== ============ ======

Expected data transfer for the sources
--------------------------------------
=========================== ========
Number of tasks to generate 1       
Sent data                   9.32 KB 
Total received data         12.34 KB
Maximum received per task   12.34 KB
=========================== ========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         PointSource  0.150  1         1.240E-04   0.0        0.004    
0            2         PointSource  0.150  1         8.893E-05   0.0        0.004    
0            3         PointSource  0.150  1         8.178E-05   0.0        0.004    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_gmfs_and_curves  0.071     0.0       8     
compute poes                   0.057     0.0       8     
total compute_ruptures         0.013     0.0       1     
make contexts                  0.010     0.0       8     
saving gmfs                    0.009     0.0       8     
reading composite source model 0.006     0.0       1     
managing sources               0.002     0.0       1     
saving ruptures                0.002     0.0       1     
store source_info              0.001     0.0       1     
aggregate curves               6.950E-04 0.0       1     
filtering sources              2.947E-04 0.0       3     
reading site collection        3.791E-05 0.0       1     
============================== ========= ========= ======