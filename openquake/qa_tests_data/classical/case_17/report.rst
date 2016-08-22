Classical Hazard QA Test, Case 17
=================================

gem-tstation:/home/michele/ssd/calc_40694.hdf5 updated Mon Aug 22 12:45:45 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================
calculation_mode             'classical'                     
number_of_logic_tree_samples 5                               
maximum_distance             {u'active shallow crust': 200.0}
investigation_time           1000.0                          
ses_per_logic_tree_path      1                               
truncation_level             2.0                             
rupture_mesh_spacing         1.0                             
complex_fault_mesh_spacing   1.0                             
width_of_mfd_bin             1.0                             
area_source_discretization   10.0                            
random_seed                  106                             
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
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ========================================== =============== ================
smlt_path weight source_model_file                          gsim_logic_tree num_realizations
========= ====== ========================================== =============== ================
b1        0.200  `source_model_1.xml <source_model_1.xml>`_ trivial(1)      1/1             
b2        0.200  `source_model_2.xml <source_model_2.xml>`_ trivial(1)      4/1             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================== ============= ============= ==========
grp_id gsims                distances     siteparams    ruptparams
====== ==================== ============= ============= ==========
0      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
1      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
====== ==================== ============= ============= ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=5)
  0,SadighEtAl1997(): ['<0,b1~b1,w=0.2>']
  1,SadighEtAl1997(): ['<1,b2~b1,w=0.2>', '<2,b2~b1,w=0.2>', '<3,b2~b1,w=0.2>', '<4,b2~b1,w=0.2>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ======
source_model       grp_id trt                  num_sources eff_ruptures weight
================== ====== ==================== =========== ============ ======
source_model_1.xml 0      Active Shallow Crust 1           39           0.975 
source_model_2.xml 1      Active Shallow Crust 1           7            0.175 
================== ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   46   
filtered_weight 1.150
=============== =====

Informational data
------------------
=============================== ============
classical_max_received_per_task 1,798       
classical_num_tasks             2           
classical_sent.monitor          1,616       
classical_sent.rlzs_by_gsim     1,302       
classical_sent.sitecol          866         
classical_sent.sources          2,661       
classical_tot_received          3,596       
hazard.input_weight             1.675       
hazard.n_imts                   1           
hazard.n_levels                 3.000       
hazard.n_realizations           5           
hazard.n_sites                  1           
hazard.n_sources                2           
hazard.output_weight            15          
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            1         PointSource  0.975  1         6.604E-05   0.0        0.059         0.059         1        
1            2         PointSource  0.175  1         1.907E-05   0.0        0.013         0.013         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  8.512E-05   0.0        0.072         0.072         2         2     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  0.038 0.032  0.016 0.061 2        
classical.memory_mb 1.412 0.003  1.410 1.414 2        
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                0.077     1.414     2     
making contexts                0.036     0.0       46    
computing poes                 0.009     0.0       46    
reading composite source model 0.008     0.0       1     
store source_info              0.006     0.0       1     
managing sources               0.005     0.0       1     
saving probability maps        0.002     0.0       1     
read poes                      9.871E-04 0.0       1     
filtering sources              8.512E-05 0.0       2     
reading site collection        4.601E-05 0.0       1     
aggregate curves               3.481E-05 0.0       2     
============================== ========= ========= ======