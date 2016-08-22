Classical Hazard QA Test, Case 1
================================

gem-tstation:/home/michele/ssd/calc_40733.hdf5 updated Mon Aug 22 13:03:38 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================
calculation_mode             'classical'                     
number_of_logic_tree_samples 0                               
maximum_distance             {u'active shallow crust': 200.0}
investigation_time           1.0                             
ses_per_logic_tree_path      1                               
truncation_level             2.0                             
rupture_mesh_spacing         1.0                             
complex_fault_mesh_spacing   1.0                             
width_of_mfd_bin             1.0                             
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
source_model.xml 0      Active Shallow Crust 1           1            0.025 
================ ====== ==================== =========== ============ ======

Informational data
------------------
=============================== ============
classical_max_received_per_task 1,918       
classical_num_tasks             1           
classical_sent.monitor          903         
classical_sent.rlzs_by_gsim     516         
classical_sent.sitecol          433         
classical_sent.sources          1,188       
classical_tot_received          1,918       
hazard.input_weight             0.025       
hazard.n_imts                   2           
hazard.n_levels                 3.000       
hazard.n_realizations           1           
hazard.n_sites                  1           
hazard.n_sources                1           
hazard.output_weight            6.000       
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            1         PointSource  0.025  1         3.004E-05   0.0        0.002         0.002         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  3.004E-05   0.0        0.002         0.002         1         1     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  0.003 NaN    0.003 0.003 1        
classical.memory_mb 0.0   NaN    0.0   0.0   1        
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
store source_info              0.006     0.0       1     
reading composite source model 0.005     0.0       1     
managing sources               0.003     0.0       1     
total classical                0.003     0.0       1     
saving probability maps        0.001     0.0       1     
making contexts                9.911E-04 0.0       1     
read poes                      5.839E-04 0.0       1     
computing poes                 4.220E-04 0.0       1     
reading site collection        3.695E-05 0.0       1     
filtering sources              3.004E-05 0.0       1     
aggregate curves               1.812E-05 0.0       1     
============================== ========= ========= ======