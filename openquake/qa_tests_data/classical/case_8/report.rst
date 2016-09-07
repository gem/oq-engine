Classical Hazard QA Test, Case 8
================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_48436.hdf5 Wed Sep  7 16:05:06 2016
engine_version                                 2.1.0-gitfaa2965        
hazardlib_version                              0.21.0-git89bccaf       
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
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           3000         75    
source_model.xml 1      Active Shallow Crust 1           3000         75    
source_model.xml 2      Active Shallow Crust 1           3000         75    
================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     3    
#sources        3    
#eff_ruptures   9,000
filtered_weight 225  
=============== =====

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,129       
count_eff_ruptures_num_tasks             3           
count_eff_ruptures_sent.gsims            246         
count_eff_ruptures_sent.monitor          2,733       
count_eff_ruptures_sent.sitecol          1,299       
count_eff_ruptures_sent.sources          3,594       
count_eff_ruptures_tot_received          3,387       
hazard.input_weight                      225         
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
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
2            1         PointSource  75     1         0.0         1.950E-04  0.0           0.0           0        
0            1         PointSource  75     1         0.0         1.848E-04  0.0           0.0           0        
1            1         PointSource  75     1         0.0         1.509E-04  0.0           0.0           0        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  0.0         5.307E-04  0.0           0.0           0         3     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 3.793E-04 1.037E-05 3.691E-04 3.898E-04 3        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.021     0.0       1     
reading composite source model 0.017     0.0       1     
total count_eff_ruptures       0.001     0.0       3     
aggregate curves               8.702E-05 0.0       3     
saving probability maps        3.600E-05 0.0       1     
reading site collection        3.195E-05 0.0       1     
store source_info              1.192E-05 0.0       1     
============================== ========= ========= ======