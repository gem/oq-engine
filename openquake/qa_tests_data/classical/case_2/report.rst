Classical Hazard QA Test, Case 2
================================

gem-tstation:/home/michele/ssd/calc_40693.hdf5 updated Mon Aug 22 12:45:45 2016

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
engine_version               '2.1.0-git8cbb23e'              
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
====== ==================== ============= ============= ==========
grp_id gsims                distances     siteparams    ruptparams
====== ==================== ============= ============= ==========
0      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
====== ==================== ============= ============= ==========

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
=============================== ============
classical_max_received_per_task 1,823       
classical_num_tasks             1           
classical_sent.monitor          817         
classical_sent.rlzs_by_gsim     516         
classical_sent.sitecol          433         
classical_sent.sources          1,200       
classical_tot_received          1,823       
hazard.input_weight             75          
hazard.n_imts                   1           
hazard.n_levels                 4.000       
hazard.n_realizations           1           
hazard.n_sites                  1           
hazard.n_sources                1           
hazard.output_weight            4.000       
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            1         PointSource  75     1         0.004       6.890E-05  2.538         2.538         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  0.004       6.890E-05  2.538         2.538         1         1     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  2.540 NaN    2.540 2.540 1        
classical.memory_mb 1.711 NaN    1.711 1.711 1        
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                2.540     1.711     1     
making contexts                1.219     0.0       3,000 
computing poes                 0.248     0.0       3,000 
managing sources               0.026     0.0       1     
store source_info              0.010     0.0       1     
reading composite source model 0.010     0.0       1     
filtering sources              0.004     0.0       1     
saving probability maps        0.003     0.0       1     
read poes                      8.259E-04 0.0       1     
splitting sources              6.890E-05 0.0       1     
reading site collection        5.317E-05 0.0       1     
aggregate curves               4.911E-05 0.0       1     
============================== ========= ========= ======