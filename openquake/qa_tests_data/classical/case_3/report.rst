Classical Hazard QA Test, Case 3
================================

thinkpad:/home/michele/oqdata/calc_16930.hdf5 updated Wed Aug 24 04:50:38 2016

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
engine_version               '2.1.0-git74bd74a'              
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
======================================== =========
count_eff_ruptures_max_received_per_task 1,193    
count_eff_ruptures_num_tasks             9        
count_eff_ruptures_sent.monitor          7,767    
count_eff_ruptures_sent.rlzs_by_gsim     4,644    
count_eff_ruptures_sent.sitecol          3,897    
count_eff_ruptures_sent.sources          6,880,644
count_eff_ruptures_tot_received          10,736   
hazard.input_weight                      783      
hazard.n_imts                            1        
hazard.n_levels                          3.000    
hazard.n_realizations                    1        
hazard.n_sites                           1        
hazard.n_sources                         1        
hazard.output_weight                     3.000    
hostname                                 thinkpad 
======================================== =========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            1         AreaSource   783    31,353    0.002       5.330      0.0           0.0           0        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   0.002       5.330      0.0           0.0           0         1     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               6.580     0.0       1     
splitting sources              5.330     0.0       1     
reading composite source model 5.138     0.0       1     
total count_eff_ruptures       0.026     0.0       9     
store source_info              0.005     0.0       1     
filtering sources              0.002     0.0       1     
aggregate curves               1.962E-04 0.0       9     
saving probability maps        6.700E-05 0.0       1     
reading site collection        4.196E-05 0.0       1     
============================== ========= ========= ======