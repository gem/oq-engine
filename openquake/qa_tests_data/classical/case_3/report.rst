Classical Hazard QA Test, Case 3
================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_54410.hdf5 Tue Sep 27 14:06:48 2016
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
rupture_mesh_spacing         1.0                             
complex_fault_mesh_spacing   1.0                             
width_of_mfd_bin             1.0                             
area_source_discretization   0.05                            
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
source_model.xml 0      Active Shallow Crust 1           31353        783   
================ ====== ==================== =========== ============ ======

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,239       
count_eff_ruptures_num_tasks             4           
count_eff_ruptures_sent.gsims            328         
count_eff_ruptures_sent.monitor          4,072       
count_eff_ruptures_sent.sitecol          1,732       
count_eff_ruptures_sent.sources          7,222,467   
count_eff_ruptures_tot_received          4,956       
hazard.input_weight                      783         
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
====== ========= ============ ====== ========= =========
grp_id source_id source_class weight calc_time num_sites
====== ========= ============ ====== ========= =========
0      1         AreaSource   783    0.0       0        
====== ========= ============ ====== ========= =========

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
count_eff_ruptures 0.159 0.002  0.157 0.162 4        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               6.202     0.0       1     
filter/split heavy sources     6.186     0.0       1     
reading composite source model 3.645     0.0       1     
total count_eff_ruptures       0.636     25        4     
store source_info              8.512E-04 0.0       1     
aggregate curves               7.463E-05 0.0       4     
saving probability maps        4.292E-05 0.0       1     
reading site collection        3.600E-05 0.0       1     
============================== ========= ========= ======