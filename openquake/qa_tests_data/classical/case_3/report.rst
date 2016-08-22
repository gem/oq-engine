Classical Hazard QA Test, Case 3
================================

gem-tstation:/home/michele/ssd/calc_40709.hdf5 updated Mon Aug 22 12:51:05 2016

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
source_model.xml 0      Active Shallow Crust 1           31353        783   
================ ====== ==================== =========== ============ ======

Informational data
------------------
=============================== ============
classical_max_received_per_task 28,774      
classical_num_tasks             20          
classical_sent.monitor          16,180      
classical_sent.rlzs_by_gsim     10,320      
classical_sent.sitecol          8,660       
classical_sent.sources          6,885,698   
classical_tot_received          564,425     
hazard.input_weight             783         
hazard.n_imts                   1           
hazard.n_levels                 3.000       
hazard.n_realizations           1           
hazard.n_sites                  1           
hazard.n_sources                1           
hazard.output_weight            3.000       
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            1         AreaSource   783    31,353    0.001       3.972      28            0.029         31,353   
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   0.001       3.972      28            0.029         31,353    1     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  1.554 0.229  0.842 2.025 20       
classical.memory_mb 0.025 0.078  0.0   0.254 20       
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                31        0.254     20    
making contexts                14        0.0       31,353
managing sources               4.902     0.0       1     
splitting sources              3.972     0.0       1     
reading composite source model 3.811     0.0       1     
computing poes                 2.885     0.0       31,353
store source_info              0.393     0.0       1     
saving probability maps        0.002     0.0       1     
filtering sources              0.001     0.0       1     
aggregate curves               7.641E-04 0.0       20    
read poes                      5.491E-04 0.0       1     
reading site collection        3.314E-05 0.0       1     
============================== ========= ========= ======