Classical Hazard QA Test, Case 9
================================

============================================ ========================
gem-tstation:/mnt/ssd/oqdata/calc_85559.hdf5 Tue Feb 14 15:40:06 2017
engine_version                               2.3.0-git1f56df2        
hazardlib_version                            0.23.0-git6937706       
============================================ ========================

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
source                  `7.0 <7.0>`_                                                
source                  `7.5 <7.5>`_                                                
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
source_model.xml 1      Active Shallow Crust 1           3500         3,500       
================ ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      2    
#eff_ruptures 6,500
#tot_ruptures 6,500
#tot_weight   650  
============= =====

Informational data
------------------
=========================================== ============
count_eff_ruptures_max_received_per_task    1,289       
count_eff_ruptures_num_tasks                2           
count_eff_ruptures_sent.gsims               182         
count_eff_ruptures_sent.monitor             2,126       
count_eff_ruptures_sent.sources             2,360       
count_eff_ruptures_sent.srcfilter           1,420       
count_eff_ruptures_tot_received             2,578       
hazard.input_weight                         650         
hazard.n_imts                               1           
hazard.n_levels                             4           
hazard.n_realizations                       2           
hazard.n_sites                              1           
hazard.n_sources                            2           
hazard.output_weight                        8.000       
hostname                                    gem-tstation
require_epsilons                            False       
=========================================== ============

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         PointSource  3,000        0.0       1         0        
1      1         PointSource  3,500        0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.0       2     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 2.059 0.190  1.924 2.194 2        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         4.118     0.781     2     
reading composite source model   0.025     0.0       1     
filtering composite source model 0.020     0.0       1     
managing sources                 0.005     0.0       1     
store source_info                0.001     0.0       1     
aggregate curves                 6.795E-05 0.0       2     
reading site collection          6.318E-05 0.0       1     
saving probability maps          4.745E-05 0.0       1     
================================ ========= ========= ======