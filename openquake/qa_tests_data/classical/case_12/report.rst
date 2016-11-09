Classical Hazard QA Test, Case 12
=================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_66993.hdf5 Wed Nov  9 08:15:47 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ==============================================================
calculation_mode             'classical'                                                   
number_of_logic_tree_samples 0                                                             
maximum_distance             {u'stable continental': 200.0, u'active shallow crust': 200.0}
investigation_time           1.0                                                           
ses_per_logic_tree_path      1                                                             
truncation_level             2.0                                                           
rupture_mesh_spacing         1.0                                                           
complex_fault_mesh_spacing   1.0                                                           
width_of_mfd_bin             1.0                                                           
area_source_discretization   10.0                                                          
random_seed                  1066                                                          
master_seed                  0                                                             
sites_per_tile               10000                                                         
============================ ==============================================================

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
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1,1)    1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      SadighEtAl1997()    rrup      vs30       rake mag  
1      BooreAtkinson2008() rjb       vs30       rake mag  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,SadighEtAl1997(): ['<0,b1~b1_b2,w=1.0>']
  1,BooreAtkinson2008(): ['<0,b1~b1_b2,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           1            1           
source_model.xml 1      Stable Continental   1           1            1           
================ ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      2    
#eff_ruptures 2    
#tot_ruptures 2    
#tot_weight   0.200
============= =====

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,284       
count_eff_ruptures_num_tasks             2           
count_eff_ruptures_sent.gsims            175         
count_eff_ruptures_sent.monitor          2,094       
count_eff_ruptures_sent.sitecol          866         
count_eff_ruptures_sent.sources          2,400       
count_eff_ruptures_tot_received          2,568       
hazard.input_weight                      0.200       
hazard.n_imts                            1           
hazard.n_levels                          3           
hazard.n_realizations                    1           
hazard.n_sites                           1           
hazard.n_sources                         2           
hazard.output_weight                     3.000       
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
1      2         PointSource  1            0.0       1         0        
0      1         PointSource  1            0.0       1         0        
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
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 6.596E-04 2.883E-05 6.392E-04 6.800E-04 2        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.004     0.0       1     
filtering composite source model 0.003     0.0       1     
managing sources                 0.003     0.0       1     
total count_eff_ruptures         0.001     0.0       2     
store source_info                9.320E-04 0.0       1     
aggregate curves                 5.293E-05 0.0       2     
saving probability maps          3.791E-05 0.0       1     
reading site collection          2.694E-05 0.0       1     
================================ ========= ========= ======