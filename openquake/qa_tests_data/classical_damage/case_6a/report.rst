Classical PSHA-Based Hazard
===========================

gem-tstation:/home/michele/ssd/calc_40539.hdf5 updated Mon Aug 22 12:15:16 2016

num_sites = 7, sitecol = 1015 B

Parameters
----------
============================ ================================
calculation_mode             'classical_damage'              
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           50.0                            
ses_per_logic_tree_path      1                               
truncation_level             3.0                             
rupture_mesh_spacing         1.0                             
complex_fault_mesh_spacing   1.0                             
width_of_mfd_bin             0.1                             
area_source_discretization   20.0                            
random_seed                  42                              
master_seed                  0                               
sites_per_tile               10000                           
engine_version               '2.1.0-git8cbb23e'              
============================ ================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job_haz.ini <job_haz.ini>`_                                
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_fragility    `fragility_model.xml <fragility_model.xml>`_                
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
source_model.xml 0      Active Shallow Crust 1           1694         1,694 
================ ====== ==================== =========== ============ ======

Informational data
------------------
=============================== ============
classical_max_received_per_task 6,591       
classical_num_tasks             13          
classical_sent.monitor          62,608      
classical_sent.rlzs_by_gsim     6,695       
classical_sent.sitecol          7,189       
classical_sent.sources          14,667      
classical_tot_received          85,523      
hazard.input_weight             1,694       
hazard.n_imts                   1           
hazard.n_levels                 8.000       
hazard.n_realizations           1           
hazard.n_sites                  7           
hazard.n_sources                1           
hazard.output_weight            56          
hostname                        gem-tstation
require_epsilons                False       
=============================== ============

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
Wood     1.000 0.0    1   1   7         7         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class      weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ================= ====== ========= =========== ========== ============= ============= =========
0            1         SimpleFaultSource 1,694  15        0.002       0.071      6.299         0.558         15       
============ ========= ================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================= =========== ========== ============= ============= ========= ======
source_class      filter_time split_time cum_calc_time max_calc_time num_tasks counts
================= =========== ========== ============= ============= ========= ======
SimpleFaultSource 0.002       0.071      6.299         0.558         15        1     
================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  0.488 0.093  0.238 0.562 13       
classical.memory_mb 0.011 0.028  0.0   0.102 13       
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                6.341     0.102     13    
making contexts                5.772     0.0       1,694 
computing poes                 0.243     0.0       1,694 
managing sources               0.094     0.0       1     
splitting sources              0.071     0.0       1     
store source_info              0.011     0.0       1     
reading composite source model 0.011     0.0       1     
reading exposure               0.004     0.0       1     
saving probability maps        0.002     0.0       1     
filtering sources              0.002     0.0       1     
aggregate curves               8.330E-04 0.0       13    
reading site collection        9.060E-06 0.0       1     
============================== ========= ========= ======