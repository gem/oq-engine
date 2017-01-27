Classical Hazard QA Test, Case 3
================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_81063.hdf5 Thu Jan 26 14:29:22 2017
engine_version                                 2.3.0-gite807292        
hazardlib_version                              0.23.0-gite1ea7ea       
============================================== ========================

num_sites = 1, sitecol = 762 B

Parameters
----------
=============================== ===============================
calculation_mode                'classical'                    
number_of_logic_tree_samples    0                              
maximum_distance                {'active shallow crust': 200.0}
investigation_time              1.0                            
ses_per_logic_tree_path         1                              
truncation_level                0.0                            
rupture_mesh_spacing            1.0                            
complex_fault_mesh_spacing      1.0                            
width_of_mfd_bin                1.0                            
area_source_discretization      0.05                           
ground_motion_correlation_model None                           
random_seed                     1066                           
master_seed                     0                              
=============================== ===============================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           31353        31,353      
================ ====== ==================== =========== ============ ============

Informational data
------------------
=========================================== ============
count_eff_ruptures_max_received_per_task    1,218       
count_eff_ruptures_num_tasks                16          
count_eff_ruptures_sent.gsims               1,456       
count_eff_ruptures_sent.monitor             15,872      
count_eff_ruptures_sent.sitecol             9,568       
count_eff_ruptures_sent.sources             6,454,672   
count_eff_ruptures_tot_received             19,482      
hazard.input_weight                         3,135       
hazard.n_imts                               1           
hazard.n_levels                             3           
hazard.n_realizations                       1           
hazard.n_sites                              1           
hazard.n_sources                            1           
hazard.output_weight                        3.000       
hostname                                    gem-tstation
require_epsilons                            False       
=========================================== ============

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         AreaSource   31,353       0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       1     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.053 0.027  0.015 0.081 16       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
managing sources                 21        0.0       1     
split/filter heavy sources       21        0.0       1     
reading composite source model   3.852     0.0       1     
total count_eff_ruptures         0.840     6.215     16    
filtering composite source model 8.929E-04 0.0       1     
store source_info                5.255E-04 0.0       1     
aggregate curves                 2.134E-04 0.0       16    
reading site collection          4.244E-05 0.0       1     
saving probability maps          2.360E-05 0.0       1     
================================ ========= ========= ======