Classical Hazard QA Test, Case 7
================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_66990.hdf5 Wed Nov  9 08:15:36 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
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
width_of_mfd_bin             1.0                             
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
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ========================================== =============== ================
smlt_path weight source_model_file                          gsim_logic_tree num_realizations
========= ====== ========================================== =============== ================
b1        0.700  `source_model_1.xml <source_model_1.xml>`_ trivial(1)      1/1             
b2        0.300  `source_model_2.xml <source_model_2.xml>`_ trivial(1)      1/1             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       rake mag  
1      SadighEtAl1997() rrup      vs30       rake mag  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,SadighEtAl1997(): ['<0,b1~b1,w=0.699999988079>']
  1,SadighEtAl1997(): ['<1,b2~b1,w=0.300000011921>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ============
source_model       grp_id trt                  num_sources eff_ruptures tot_ruptures
================== ====== ==================== =========== ============ ============
source_model_1.xml 0      Active Shallow Crust 2           1386         1,386       
source_model_2.xml 1      Active Shallow Crust 1           901          901         
================== ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      3    
#eff_ruptures 2,287
#tot_ruptures 2,287
#tot_weight   2,772
============= =====

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,255       
count_eff_ruptures_num_tasks             3           
count_eff_ruptures_sent.gsims            246         
count_eff_ruptures_sent.monitor          3,045       
count_eff_ruptures_sent.sitecol          1,731       
count_eff_ruptures_sent.sources          3,318       
count_eff_ruptures_tot_received          3,765       
hazard.input_weight                      2,772       
hazard.n_imts                            1           
hazard.n_levels                          3           
hazard.n_realizations                    2           
hazard.n_sites                           1           
hazard.n_sources                         3           
hazard.output_weight                     6.000       
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
====== ========= ================== ============ ========= ========= =========
grp_id source_id source_class       num_ruptures calc_time num_sites num_split
====== ========= ================== ============ ========= ========= =========
0      2         ComplexFaultSource 485          0.0       1         0        
0      1         SimpleFaultSource  901          0.0       1         0        
1      1         SimpleFaultSource  901          0.0       1         0        
====== ========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.0       1     
SimpleFaultSource  0.0       2     
================== ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 6.483E-04 2.039E-04 4.129E-04 7.701E-04 3        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   5.873     0.0       1     
managing sources                 5.775     0.0       1     
split/filter heavy sources       5.773     0.0       2     
filtering composite source model 0.003     0.0       1     
total count_eff_ruptures         0.002     0.0       3     
store source_info                5.400E-04 0.0       1     
aggregate curves                 4.387E-05 0.0       3     
reading site collection          3.791E-05 0.0       1     
saving probability maps          2.217E-05 0.0       1     
================================ ========= ========= ======