Classical Hazard QA Test, Case 8
================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_60094.hdf5 Tue Oct 11 06:57:15 2016
engine_version                                 2.1.0-git4e31fdd        
hazardlib_version                              0.21.0-gitab31f47       
============================================== ========================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================
calculation_mode             'classical'                     
number_of_logic_tree_samples 0                               
maximum_distance             {u'active shallow crust': 200.0}
investigation_time           1.0                             
ses_per_logic_tree_path      1                               
truncation_level             0.0                             
rupture_mesh_spacing         0.01                            
complex_fault_mesh_spacing   0.01                            
width_of_mfd_bin             0.001                           
area_source_discretization   10.0                            
random_seed                  1066                            
master_seed                  0                               
sites_per_tile               10000                           
============================ ================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `1.8 1.2 <1.8 1.2>`_                                        
source                  `2.0 1.0 <2.0 1.0>`_                                        
source                  `2.2 0.8 <2.2 0.8>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1_b2     0.300  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b3     0.300  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b4     0.400  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       rake mag  
1      SadighEtAl1997() rrup      vs30       rake mag  
2      SadighEtAl1997() rrup      vs30       rake mag  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,SadighEtAl1997(): ['<0,b1_b2~b1,w=0.30000000298>']
  1,SadighEtAl1997(): ['<1,b1_b3~b1,w=0.30000000298>']
  2,SadighEtAl1997(): ['<2,b1_b4~b1,w=0.39999999404>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           3000         3,000       
source_model.xml 1      Active Shallow Crust 1           3000         3,000       
source_model.xml 2      Active Shallow Crust 1           3000         3,000       
================ ====== ==================== =========== ============ ============

============= =====
#TRT models   3    
#sources      3    
#eff_ruptures 9,000
#tot_ruptures 9,000
#tot_weight   900  
============= =====

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,244       
count_eff_ruptures_num_tasks             3           
count_eff_ruptures_sent.gsims            246         
count_eff_ruptures_sent.monitor          3,078       
count_eff_ruptures_sent.sitecol          1,731       
count_eff_ruptures_sent.sources          3,642       
count_eff_ruptures_tot_received          3,732       
hazard.input_weight                      900         
hazard.n_imts                            1           
hazard.n_levels                          4           
hazard.n_realizations                    3           
hazard.n_sites                           1           
hazard.n_sources                         3           
hazard.output_weight                     12          
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
2      1         PointSource  3,000        0.0       1         0        
1      1         PointSource  3,000        0.0       1         0        
0      1         PointSource  3,000        0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.0       3     
============ ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 7.780E-04 1.830E-05 7.570E-04 7.901E-04 3        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.033     0.0       1     
filtering composite source model 0.026     0.0       1     
managing sources                 0.012     0.0       1     
split/filter heavy sources       0.008     0.0       3     
total count_eff_ruptures         0.002     0.0       3     
store source_info                7.582E-04 0.0       1     
aggregate curves                 7.486E-05 0.0       3     
saving probability maps          3.386E-05 0.0       1     
reading site collection          3.099E-05 0.0       1     
================================ ========= ========= ======