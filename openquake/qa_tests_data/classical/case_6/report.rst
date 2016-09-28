Classical Hazard QA Test, Case 6
================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_54405.hdf5 Tue Sep 27 14:06:34 2016
engine_version                                 2.1.0-git1ca7123        
hazardlib_version                              0.21.0-git9261682       
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
0      SadighEtAl1997() rrup      vs30       rake mag  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 2           1386         1,386 
================ ====== ==================== =========== ============ ======

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,236       
count_eff_ruptures_num_tasks             2           
count_eff_ruptures_sent.gsims            164         
count_eff_ruptures_sent.monitor          2,036       
count_eff_ruptures_sent.sitecol          866         
count_eff_ruptures_sent.sources          2,292       
count_eff_ruptures_tot_received          2,472       
hazard.input_weight                      1,386       
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
====== ========= ================== ====== ========= =========
grp_id source_id source_class       weight calc_time num_sites
====== ========= ================== ====== ========= =========
0      2         ComplexFaultSource 485    0.0       0        
0      1         SimpleFaultSource  901    0.0       0        
====== ========= ================== ====== ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.0       1     
SimpleFaultSource  0.0       1     
================== ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 6.441E-04 1.640E-04 5.281E-04 7.601E-04 2        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 5.990     0.0       1     
managing sources               5.945     0.0       1     
filter/split heavy sources     5.944     0.0       1     
total count_eff_ruptures       0.001     0.0       2     
store source_info              3.750E-04 0.0       1     
aggregate curves               3.099E-05 0.0       2     
reading site collection        3.004E-05 0.0       1     
saving probability maps        1.907E-05 0.0       1     
============================== ========= ========= ======