Classical Hazard QA Test, Case 2
================================

============================================== ================================
gem-tstation:/home/michele/ssd/calc_48275.hdf5 updated Wed Sep  7 15:56:14 2016
engine_version                                 2.1.0-git3a14ca6                
hazardlib_version                              0.21.0-git89bccaf               
============================================== ================================

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
width_of_mfd_bin             0.001                           
area_source_discretization   None                            
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
source_model.xml 0      Active Shallow Crust 1           3000         75    
================ ====== ==================== =========== ============ ======

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,129       
count_eff_ruptures_num_tasks             1           
count_eff_ruptures_sent.gsims            82          
count_eff_ruptures_sent.monitor          911         
count_eff_ruptures_sent.sitecol          433         
count_eff_ruptures_sent.sources          1,200       
count_eff_ruptures_tot_received          1,129       
hazard.input_weight                      75          
hazard.n_imts                            1           
hazard.n_levels                          4           
hazard.n_realizations                    1           
hazard.n_sites                           1           
hazard.n_sources                         1           
hazard.output_weight                     4           
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            1         PointSource  75     1         0.0         1.252E-04  0.0           0.0           0        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  0.0         1.252E-04  0.0           0.0           0         1     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =========
operation-duration mean      stddev min       max       num_tasks
count_eff_ruptures 7.641E-04 NaN    7.641E-04 7.641E-04 1        
================== ========= ====== ========= ========= =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.010     0.0       1     
managing sources               0.007     0.0       1     
total count_eff_ruptures       7.641E-04 0.0       1     
reading site collection        3.409E-05 0.0       1     
saving probability maps        2.503E-05 0.0       1     
aggregate curves               2.003E-05 0.0       1     
store source_info              8.106E-06 0.0       1     
============================== ========= ========= ======