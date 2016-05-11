Event-based PSHA with logic tree sampling
=========================================

gem-tstation:/home/michele/ssd/calc_16112.hdf5 updated Wed May 11 14:30:37 2016

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ===================
calculation_mode             'event_based'      
number_of_logic_tree_samples 10                 
maximum_distance             {'default': 200.0} 
investigation_time           50.0               
ses_per_logic_tree_path      200                
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             0.2                
area_source_discretization   20.0               
random_seed                  23                 
master_seed                  0                  
oqlite_version               '0.13.0-git7639915'
============================ ===================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model1.xml <source_model1.xml>`_                    
source                  `source_model2.xml <source_model2.xml>`_                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ======================================== =============== ================
smlt_path weight source_model_file                        gsim_logic_tree num_realizations
========= ====== ======================================== =============== ================
b11       0.100  `source_model1.xml <source_model1.xml>`_ simple(3)       7/7             
b12       0.100  `source_model2.xml <source_model2.xml>`_ simple(3)       3/3             
========= ====== ======================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ============================= =================
trt_id gsims                                                         distances   siteparams                    ruptparams       
====== ============================================================= =========== ============================= =================
0      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rx rjb rrup z2pt5 vs30measured vs30 z1pt0 ztor mag rake dip
1      BooreAtkinson2008() CampbellBozorgnia2008()                   rjb rrup    z2pt5 vs30                    ztor mag rake dip
====== ============================================================= =========== ============================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=10)
  0,BooreAtkinson2008(): ['<3,b11,BA,w=0.1>', '<5,b11,BA,w=0.1>']
  0,CampbellBozorgnia2008(): ['<4,b11,CB,w=0.1>', '<6,b11,CB,w=0.1>']
  0,ChiouYoungs2008(): ['<0,b11,CY,w=0.1>', '<1,b11,CY,w=0.1>', '<2,b11,CY,w=0.1>']
  1,BooreAtkinson2008(): ['<8,b12,BA,w=0.1>', '<9,b12,BA,w=0.1>']
  1,CampbellBozorgnia2008(): ['<7,b12,CB,w=0.1>']>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== =========== ============ ======
source_model      trt_id trt                  num_sources eff_ruptures weight
================= ====== ==================== =========== ============ ======
source_model1.xml 0      Active Shallow Crust 1           1,964        61    
source_model2.xml 1      Active Shallow Crust 1           694          61    
================= ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   2,658
filtered_weight 122  
=============== =====

Informational data
------------------
======== ==============
hostname 'gem-tstation'
======== ==============

Specific information for event based
------------------------------------
======================== ======
Total number of ruptures 2,658 
Total number of events   10,802
Rupture multiplicity     4.064 
======================== ======

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         AreaSource   61     307       0.001       0.068      2.411    
1            1         AreaSource   61     307       0.001       0.066      1.702    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
AreaSource   0.003       0.134      4.113     2     
============ =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         0.109 0.038  0.008 0.172 38       
compute_ruptures.memory_mb        0.0   0.0    0.0   0.0   38       
compute_gmfs_and_curves.time_sec  0.708 0.327  0.383 1.645 21       
compute_gmfs_and_curves.memory_mb 0.053 0.159  0.0   0.691 21       
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_gmfs_and_curves  14        0.691     21    
compute poes                   12        0.0       2,658 
total compute_ruptures         4.131     0.0       38    
saving ruptures                1.905     0.0       1     
make contexts                  1.724     0.0       2,658 
filtering ruptures             0.842     0.0       2,658 
bulding hazard curves          0.453     0.0       21    
managing sources               0.289     0.0       1     
reading composite source model 0.147     0.0       1     
splitting sources              0.134     0.0       2     
aggregating hcurves            0.128     0.0       143   
aggregate curves               0.029     0.0       181   
store source_info              0.011     0.0       1     
filtering sources              0.003     0.0       2     
reading site collection        4.601E-05 0.0       1     
============================== ========= ========= ======