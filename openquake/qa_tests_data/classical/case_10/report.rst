Classical Hazard QA Test, Case 10
=================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_21320.hdf5 Fri May 12 10:45:45 2017
engine_version                                   2.4.0-git59713b5        
hazardlib_version                                0.24.0-git0596dd3       
================================================ ========================

num_sites = 1, sitecol = 809 B

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.01              
complex_fault_mesh_spacing      0.01              
width_of_mfd_bin                0.001             
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     1066              
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `0.0 <0.0>`_                                                
source                  `0.4 <0.4>`_                                                
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1_b2     0.500  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b3     0.500  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,SadighEtAl1997(): ['<0,b1_b2~b1,w=0.5>']
  1,SadighEtAl1997(): ['<1,b1_b3~b1,w=0.5>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           3000         3,000       
source_model.xml 1      Active Shallow Crust 1           3000         3,000       
================ ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      2    
#eff_ruptures 6,000
#tot_ruptures 6,000
#tot_weight   600  
============= =====

Informational data
------------------
============================== =============================================================================
count_eff_ruptures.received    tot 2.16 KB, max_per_task 1.08 KB                                            
count_eff_ruptures.sent        sources 2.27 KB, monitor 1.68 KB, srcfilter 1.34 KB, gsims 182 B, param 130 B
hazard.input_weight            600                                                                          
hazard.n_imts                  1 B                                                                          
hazard.n_levels                4 B                                                                          
hazard.n_realizations          2 B                                                                          
hazard.n_sites                 1 B                                                                          
hazard.n_sources               2 B                                                                          
hazard.output_weight           4.000                                                                        
hostname                       tstation.gem.lan                                                             
require_epsilons               0 B                                                                          
============================== =============================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
1      1         PointSource  3,000        0.063     1         1        
0      1         PointSource  3,000        0.046     1         1        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.109     2     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.055 0.012  0.046 0.064 2        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         0.110     1.570     2     
reading composite source model   0.012     0.0       1     
managing sources                 0.002     0.0       1     
store source_info                7.067E-04 0.0       1     
aggregate curves                 6.366E-05 0.0       2     
filtering composite source model 5.341E-05 0.0       1     
reading site collection          4.148E-05 0.0       1     
saving probability maps          3.219E-05 0.0       1     
================================ ========= ========= ======