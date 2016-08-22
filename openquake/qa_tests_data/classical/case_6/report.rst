Classical Hazard QA Test, Case 6
================================

gem-tstation:/home/michele/ssd/calc_40697.hdf5 updated Mon Aug 22 12:50:40 2016

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
source_model.xml 0      Active Shallow Crust 2           1386         1,386 
================ ====== ==================== =========== ============ ======

Informational data
------------------
=============================== ============
classical_max_received_per_task 1,807       
classical_num_tasks             2           
classical_sent.monitor          1,618       
classical_sent.rlzs_by_gsim     1,032       
classical_sent.sitecol          866         
classical_sent.sources          2,268       
classical_tot_received          3,614       
hazard.input_weight             1,386       
hazard.n_imts                   1           
hazard.n_levels                 3.000       
hazard.n_realizations           1           
hazard.n_sites                  1           
hazard.n_sources                2           
hazard.output_weight            3.000       
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ================== ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class       weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ================== ====== ========= =========== ========== ============= ============= =========
0            2         ComplexFaultSource 485    1         0.001       5.983      278           278           1        
0            1         SimpleFaultSource  901    1         0.001       0.540      133           133           1        
============ ========= ================== ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================== =========== ========== ============= ============= ========= ======
source_class       filter_time split_time cum_calc_time max_calc_time num_tasks counts
================== =========== ========== ============= ============= ========= ======
ComplexFaultSource 0.001       5.983      278           278           1         1     
SimpleFaultSource  0.001       0.540      133           133           1         1     
================== =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== === =========
measurement         mean  stddev min   max num_tasks
classical.time_sec  206   102    133   278 2        
classical.memory_mb 9.094 1.757  7.852 10  2        
=================== ===== ====== ===== === =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                412       10        2     
making contexts                269       0.0       1,386 
reading composite source model 6.651     0.0       1     
managing sources               6.530     0.0       1     
splitting sources              6.523     0.0       2     
computing poes                 0.127     0.0       1,386 
store source_info              0.011     0.0       1     
filtering sources              0.003     0.0       2     
saving probability maps        0.002     0.0       1     
read poes                      9.041E-04 0.0       1     
aggregate curves               8.321E-05 0.0       2     
reading site collection        3.505E-05 0.0       1     
============================== ========= ========= ======