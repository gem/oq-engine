Classical Hazard QA Test, Case 5
================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_60101.hdf5 Tue Oct 11 06:57:45 2016
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
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           485          485         
================ ====== ==================== =========== ============ ============

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,236       
count_eff_ruptures_num_tasks             1           
count_eff_ruptures_sent.gsims            82          
count_eff_ruptures_sent.monitor          1,018       
count_eff_ruptures_sent.sitecol          577         
count_eff_ruptures_sent.sources          1,190       
count_eff_ruptures_tot_received          1,236       
hazard.input_weight                      970         
hazard.n_imts                            1           
hazard.n_levels                          3           
hazard.n_realizations                    1           
hazard.n_sites                           1           
hazard.n_sources                         1           
hazard.output_weight                     3.000       
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
====== ========= ================== ============ ========= ========= =========
grp_id source_id source_class       num_ruptures calc_time num_sites num_split
====== ========= ================== ============ ========= ========= =========
0      1         ComplexFaultSource 485          0.0       1         0        
====== ========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.0       1     
================== ========= ======

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =========
operation-duration mean      stddev min       max       num_tasks
count_eff_ruptures 3.929E-04 NaN    3.929E-04 3.929E-04 1        
================== ========= ====== ========= ========= =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   5.657     0.0       1     
managing sources                 5.346     0.0       1     
split/filter heavy sources       5.344     0.0       1     
filtering composite source model 0.001     0.0       1     
store source_info                4.799E-04 0.0       1     
total count_eff_ruptures         3.929E-04 0.0       1     
reading site collection          3.195E-05 0.0       1     
saving probability maps          1.907E-05 0.0       1     
aggregate curves                 1.693E-05 0.0       1     
================================ ========= ========= ======